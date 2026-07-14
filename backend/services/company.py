import re
import io
from datetime import datetime, timezone, date
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import get_jwt_identity

from models import (
    db, User, CompanyProfile, Branch, StudentProfile,
    PlacementDrive, PlacementDriveStatus, drive_branches,
    Application, ApplicationStatus,
    InterviewSchedule, InterviewStatus,
)
from serializers import company_to_dict, drive_to_dict, application_to_dict, interview_to_dict
from utils import role_required, error, apply_password_change
from app import cache

company_bp = Blueprint('company', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\d{7,15}$')
# Allowed forward-only status transitions a company can apply via the pipeline endpoint;
# rejection is handled separately.
NEXT_STAGE = {
    ApplicationStatus.APPLIED: ApplicationStatus.SHORTLISTED,
    ApplicationStatus.SHORTLISTED: ApplicationStatus.INTERVIEW,
}


def current_company():
    # Resolves the CompanyProfile for the logged-in JWT's user.
    user = User.query.get(int(get_jwt_identity()))
    return user.company_profile


def own_drive_or_404(drive_id):
    # Returns the drive only if it belongs to the current company, else None.
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_company().id:
        return None
    return drive


def own_application_or_404(application_id):
    # Returns the application only if its drive belongs to the current company, else None.
    application = Application.query.get_or_404(application_id)
    if application.drive.company_id != current_company().id:
        return None
    return application


# ---- Overview ----

@company_bp.route('/overview', methods=['GET'])
@role_required('COMPANY')
def overview():
    # Returns the company's profile plus every one of its drives with an applicant count.
    company = current_company()
    drives = [dict(drive_to_dict(d), applicant_count=len(d.applications)) for d in company.drives]
    return jsonify({'profile': company_to_dict(company), 'drives': drives})


# ---- Placement Drives ----

@company_bp.route('/drives', methods=['GET'])
@role_required('COMPANY')
def list_drives():
    # Lists this company's own drives, filterable by status/skills/CGPA/branch.
    company = current_company()
    q = PlacementDrive.query.filter_by(company_id=company.id)
    statuses = [s for s in request.args.get('status', '').split(',') if s]
    if statuses:
        q = q.filter(PlacementDrive.status.in_([PlacementDriveStatus[s] for s in statuses if s in PlacementDriveStatus.__members__]))
    skills = request.args.get('skills', '').strip()
    if skills:
        q = q.filter(PlacementDrive.skills_required.ilike(f'%{skills}%'))
    min_cgpa = request.args.get('min_cgpa')
    if min_cgpa:
        q = q.filter(PlacementDrive.cgpa >= float(min_cgpa))
    branches = [b for b in request.args.get('branches', '').split(',') if b]
    if branches:
        q = q.join(drive_branches).join(Branch).filter(Branch.name.in_(branches))
    drives = q.order_by(PlacementDrive.created_at.desc()).all()
    return jsonify({'count': len(drives), 'results': [drive_to_dict(d) for d in drives]})


def validate_drive_payload(data):
    # Validates a create/update drive payload, collecting every error found rather than stopping at the first one.
    errors = []
    if not (data.get('job_title') or '').strip():
        errors.append('Job title is required.')
    try:
        cgpa = float(data.get('cgpa'))
        if cgpa < 0 or cgpa > 10:
            raise ValueError()
    except (TypeError, ValueError):
        errors.append('Minimum CGPA must be a number between 0.0 and 10.0.')
    try:
        deadline = datetime.fromisoformat(data.get('application_deadline'))
        now = datetime.now(timezone.utc).replace(tzinfo=deadline.tzinfo)
        if deadline <= now:
            raise ValueError()
    except (TypeError, ValueError):
        errors.append('Application deadline must be a future date.')
    try:
        min_target_year = int(data.get('min_target_year'))
        max_target_year = int(data.get('max_target_year'))
        if not (2026 <= min_target_year <= 2033) or not (2026 <= max_target_year <= 2033):
            raise ValueError()
        if min_target_year > max_target_year:
            errors.append('Minimum graduation year cannot be after maximum graduation year.')
    except (TypeError, ValueError):
        errors.append('Minimum and maximum graduation years must both be between 2026 and 2033.')
    try:
        salary = float(data.get('salary'))
        if salary <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        errors.append('Offered salary must be a positive number.')
    if not data.get('branch_ids'):
        errors.append('Please select at least one eligible branch.')
    return errors


@company_bp.route('/drives', methods=['POST'])
@role_required('COMPANY')
def create_drive():
    # Creates a new drive in PENDING status, awaiting admin approval.
    company = current_company()
    data = request.get_json(force=True) or {}
    errors = validate_drive_payload(data)
    if errors:
        return error(' '.join(errors))

    branches = Branch.query.filter(Branch.id.in_(data['branch_ids'])).all()
    drive = PlacementDrive(
        company_id=company.id,
        job_title=data['job_title'].strip(),
        job_description=data.get('job_description'),
        location=data.get('location'),
        job_type=data.get('job_type'),
        application_deadline=datetime.fromisoformat(data['application_deadline']),
        cgpa=float(data['cgpa']),
        min_target_year=int(data['min_target_year']),
        max_target_year=int(data['max_target_year']),
        skills_required=data.get('skills_required'),
        experience_required=data.get('experience_required'),
        salary=float(data['salary']),
        benefits=data.get('benefits'),
        notes=data.get('notes'),
        status=PlacementDriveStatus.PENDING,
        allowed_branches=branches,
    )
    db.session.add(drive)
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive)), 201


@company_bp.route('/drives/<int:drive_id>', methods=['PATCH'])
@role_required('COMPANY')
def update_drive(drive_id):
    # Fully replaces an editable drive's fields; editing a rejected drive resets it to PENDING so admin re-reviews it.
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    if drive.status not in (PlacementDriveStatus.PENDING, PlacementDriveStatus.REJECTED):
        return error('Only pending or rejected drives can be edited.')
    data = request.get_json(force=True) or {}
    errors = validate_drive_payload(data)
    if errors:
        return error(' '.join(errors))

    drive.job_title = data['job_title'].strip()
    drive.job_description = data.get('job_description')
    drive.location = data.get('location')
    drive.job_type = data.get('job_type')
    drive.application_deadline = datetime.fromisoformat(data['application_deadline'])
    drive.cgpa = float(data['cgpa'])
    drive.min_target_year = int(data['min_target_year'])
    drive.max_target_year = int(data['max_target_year'])
    drive.skills_required = data.get('skills_required')
    drive.experience_required = data.get('experience_required')
    drive.salary = float(data['salary'])
    drive.benefits = data.get('benefits')
    drive.notes = data.get('notes')
    drive.allowed_branches = Branch.query.filter(Branch.id.in_(data['branch_ids'])).all()
    if drive.status == PlacementDriveStatus.REJECTED:
        drive.status = PlacementDriveStatus.PENDING

    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@company_bp.route('/drives/<int:drive_id>/extend-deadline', methods=['POST'])
@role_required('COMPANY')
def extend_deadline(drive_id):
    # Sets a new future deadline on this drive; usable on any status the company owns.
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    data = request.get_json(force=True) or {}
    try:
        new_deadline = datetime.fromisoformat(data.get('application_deadline', ''))
    except ValueError:
        return error('Please provide a valid deadline date.')
    if new_deadline <= datetime.now(timezone.utc).replace(tzinfo=new_deadline.tzinfo):
        return error('The new deadline must be a future date.')
    drive.application_deadline = new_deadline
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@company_bp.route('/drives/<int:drive_id>/close', methods=['POST'])
@role_required('COMPANY')
def close_drive(drive_id):
    # Stops new applications to an approved drive without cancelling it outright.
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be closed.')
    drive.status = PlacementDriveStatus.APPLICATIONS_CLOSED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@company_bp.route('/drives/<int:drive_id>/cancel', methods=['POST'])
@role_required('COMPANY')
def cancel_drive(drive_id):
    # Cancels an approved drive and auto-rejects every application still in progress on it.
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be cancelled.')
    drive.status = PlacementDriveStatus.CANCELLED
    for application in drive.applications:
        if application.status in (ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER):
            application.status = ApplicationStatus.REJECTED
            application.feedback = 'Automatically rejected: the placement drive was cancelled.'
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


# ---- Applications ----

@company_bp.route('/applications', methods=['GET'])
@role_required('COMPANY')
def list_applications():
    # Lists applications to this company's own drives, filterable by drive, drive open/closed state, drive status, and student name.
    company = current_company()
    q = Application.query.join(PlacementDrive).filter(PlacementDrive.company_id == company.id)
    search = request.args.get('search', '').strip()
    drive_ids = [d for d in request.args.get('drive_ids', '').split(',') if d]
    if drive_ids:
        q = q.filter(Application.drive_id.in_([int(d) for d in drive_ids]))
    open_closed = request.args.get('drive_state')
    if open_closed == 'open':
        q = q.filter(PlacementDrive.status == PlacementDriveStatus.APPROVED)
    elif open_closed == 'closed':
        q = q.filter(PlacementDrive.status.in_([PlacementDriveStatus.APPLICATIONS_CLOSED, PlacementDriveStatus.CANCELLED]))
    drive_statuses = [s for s in request.args.get('drive_status', '').split(',') if s]
    if drive_statuses:
        q = q.filter(PlacementDrive.status.in_([PlacementDriveStatus[s] for s in drive_statuses if s in PlacementDriveStatus.__members__]))
    applications = q.order_by(Application.application_date.desc()).all()
    results = [application_to_dict(a, include_interviews=False) for a in applications]
    # Name search is applied after serialization since it matches against the student's display name rather than a raw column.
    if search:
        results = [r for r in results if search.lower() in r['student_name'].lower()]
    return jsonify({'count': len(results), 'results': results})


@company_bp.route('/applications/<int:application_id>', methods=['GET'])
@role_required('COMPANY')
def get_application(application_id):
    # Returns full application detail for one of this company's own applications.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    return jsonify(application_to_dict(application))


@company_bp.route('/applications/<int:application_id>/status', methods=['PATCH'])
@role_required('COMPANY')
def update_application_status(application_id):
    # Advances an application one step forward per NEXT_STAGE, or rejects it outright;
    # any other requested transition is refused.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    data = request.get_json(force=True) or {}
    target = data.get('status')
    if target == 'REJECTED':
        application.status = ApplicationStatus.REJECTED
    elif NEXT_STAGE.get(application.status) and NEXT_STAGE[application.status].name == target:
        application.status = NEXT_STAGE[application.status]
    else:
        return error('Invalid pipeline transition.')
    db.session.commit()
    return jsonify(application_to_dict(application))


@company_bp.route('/applications/<int:application_id>/schedule-interview', methods=['POST'])
@role_required('COMPANY')
def schedule_interview(application_id):
    # Creates an interview round for a shortlisted (or already interviewing) candidate.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if application.status not in (ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW):
        return error('Interviews can only be scheduled once the candidate is shortlisted.')
    data = request.get_json(force=True) or {}
    try:
        scheduled = datetime.fromisoformat(data.get('scheduled_date_time', ''))
    except ValueError:
        return error('Please provide a valid interview date and time.')
    if not (data.get('interviewer_name') or '').strip():
        return error('Interviewer name is required.')

    interview = InterviewSchedule(
        application_id=application.id,
        scheduled_date_time=scheduled,
        interviewer_name=data['interviewer_name'].strip(),
        meeting_link=data.get('meeting_link'),
        notes=data.get('notes'),
        status=InterviewStatus.SCHEDULED,
    )
    db.session.add(interview)
    # Scheduling the first interview is how a shortlisted candidate moves into the Interview stage.
    application.status = ApplicationStatus.INTERVIEW
    db.session.commit()
    return jsonify(interview_to_dict(interview)), 201


@company_bp.route('/applications/<int:application_id>/offer', methods=['POST'])
@role_required('COMPANY')
def make_offer(application_id):
    # Records an offer (salary, joining date, optional offer letter PDF) and moves the application to the Offer stage. Accepts either JSON or multipart form data.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if application.status != ApplicationStatus.INTERVIEW:
        return error('An offer can only be made once the candidate reaches the Interview stage.')

    offer_letter_b64 = None
    salary = None
    joining_date_raw = None
    if request.content_type and 'multipart/form-data' in request.content_type:
        salary = request.form.get('salary_offered')
        joining_date_raw = request.form.get('joining_date')
        file = request.files.get('offer_letter')
        if file:
            offer_letter_b64 = file.read()
    else:
        data = request.get_json(force=True) or {}
        salary = data.get('salary_offered')
        joining_date_raw = data.get('joining_date')

    try:
        salary = float(salary)
        if salary <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        return error('Offered salary must be a positive number.')
    try:
        joining = date.fromisoformat(joining_date_raw)
    except (TypeError, ValueError):
        return error('Please provide a valid joining date.')

    application.offered_salary = salary
    application.offered_joining_date = joining
    if offer_letter_b64:
        application.offer_letter = offer_letter_b64
    application.status = ApplicationStatus.OFFER
    db.session.commit()
    return jsonify(application_to_dict(application))


@company_bp.route('/applications/<int:application_id>/offer-letter', methods=['GET'])
@role_required('COMPANY')
def download_offer_letter(application_id):
    # Streams the offer letter PDF this company uploaded for this application.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if not application.offer_letter:
        return error('No offer letter uploaded yet.', 404)
    return send_file(io.BytesIO(application.offer_letter), mimetype='application/pdf', download_name='offer_letter.pdf')


@company_bp.route('/applications/<int:application_id>/resume', methods=['GET'])
@role_required('COMPANY')
def download_candidate_resume(application_id):
    # Streams the resume snapshot taken when the candidate applied, not their current profile.
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if not application.snapshot_resume:
        return error('No resume uploaded yet.', 404)
    return send_file(io.BytesIO(application.snapshot_resume), mimetype='application/pdf', download_name='resume.pdf')


# ---- Interviews ----

@company_bp.route('/interviews', methods=['GET'])
@role_required('COMPANY')
def list_interviews():
    # Lists interviews for this company's own applications, filterable by drive and candidate name, sortable by scheduled date/time.
    company = current_company()
    q = (InterviewSchedule.query
         .join(Application).join(PlacementDrive)
         .filter(PlacementDrive.company_id == company.id))
    drive_ids = [d for d in request.args.get('drive_ids', '').split(',') if d]
    if drive_ids:
        q = q.filter(Application.drive_id.in_([int(d) for d in drive_ids]))
    student_name = request.args.get('student_name', '').strip()
    order = InterviewSchedule.scheduled_date_time.asc() if request.args.get('sort') == 'oldest' else InterviewSchedule.scheduled_date_time.desc()
    interviews = q.order_by(order).all()
    results = []
    # Candidate name filtering happens after the query since it's not a raw column here.
    for interview in interviews:
        application = interview.application
        if student_name and student_name.lower() not in application.student.user.name.lower():
            continue
        payload = interview_to_dict(interview)
        payload.update({
            'student_name': application.student.user.name,
            'job_title': application.drive.job_title,
        })
        results.append(payload)
    return jsonify({'count': len(results), 'results': results})


# ---- Profile ----

@company_bp.route('/profile', methods=['GET'])
@role_required('COMPANY')
def get_profile():
    # Returns the current company's own profile.
    return jsonify(company_to_dict(current_company()))


@company_bp.route('/profile', methods=['PATCH'])
@role_required('COMPANY')
def update_profile():
    # Company details (name, contact info, etc.) are managed by the admin only;
    # a company may only change its own password from here.
    company = current_company()
    data = request.get_json(force=True) or {}

    password_error = apply_password_change(company.user, data)
    if password_error:
        return password_error

    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))
