import re
from datetime import datetime, timezone, date
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from models import (
    db, User, CompanyProfile, Branch, StudentProfile,
    PlacementDrive, PlacementDriveStatus,
    Application, ApplicationStatus,
    InterviewSchedule, InterviewStatus,
)
from serializers import company_to_dict, drive_to_dict, application_to_dict, interview_to_dict
from utils import role_required, error
from app import cache

company_bp = Blueprint('company', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\d{7,15}$')
NEXT_STAGE = {
    ApplicationStatus.APPLIED: ApplicationStatus.SHORTLISTED,
    ApplicationStatus.SHORTLISTED: ApplicationStatus.INTERVIEW,
    ApplicationStatus.INTERVIEW: ApplicationStatus.OFFER,
}


def current_company():
    user = User.query.get(int(get_jwt_identity()))
    return user.company_profile


def own_drive_or_404(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.company_id != current_company().id:
        return None
    return drive


def own_application_or_404(application_id):
    application = Application.query.get_or_404(application_id)
    if application.drive.company_id != current_company().id:
        return None
    return application


# ---- Overview ----

@company_bp.route('/overview', methods=['GET'])
@role_required('COMPANY')
def overview():
    company = current_company()
    drives = [dict(drive_to_dict(d), applicant_count=len(d.applications)) for d in company.drives]
    return jsonify({'profile': company_to_dict(company), 'drives': drives})


# ---- Placement Drives ----

@company_bp.route('/drives', methods=['GET'])
@role_required('COMPANY')
def list_drives():
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
    sort = request.args.get('sort', 'created_at')
    order = PlacementDrive.application_deadline.asc() if sort == 'deadline' else PlacementDrive.created_at.desc()
    drives = q.order_by(order).all()
    return jsonify({'count': len(drives), 'results': [drive_to_dict(d) for d in drives]})


def validate_drive_payload(data):
    errors = []
    if not (data.get('job_title') or '').strip():
        errors.append('Job title is required.')
    contact_phone = (data.get('contact_phone') or '').strip()
    if not contact_phone or not PHONE_RE.match(contact_phone):
        errors.append('Please provide a valid contact number.')
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
        target_year = int(data.get('target_year'))
        if target_year < 2026 or target_year > 2033:
            raise ValueError()
    except (TypeError, ValueError):
        errors.append('Target graduation year must be between 2026 and 2033.')
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
        contact_phone=data['contact_phone'].strip(),
        application_deadline=datetime.fromisoformat(data['application_deadline']),
        cgpa=float(data['cgpa']),
        target_year=int(data['target_year']),
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
    drive.contact_phone = data['contact_phone'].strip()
    drive.application_deadline = datetime.fromisoformat(data['application_deadline'])
    drive.cgpa = float(data['cgpa'])
    drive.target_year = int(data['target_year'])
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
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be closed.')
    drive.status = PlacementDriveStatus.CLOSED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@company_bp.route('/drives/<int:drive_id>/cancel', methods=['POST'])
@role_required('COMPANY')
def cancel_drive(drive_id):
    drive = own_drive_or_404(drive_id)
    if not drive:
        return error('Drive not found.', 404)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be cancelled.')
    drive.status = PlacementDriveStatus.CANCELLED
    for application in drive.applications:
        if application.status in (ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER):
            application.status = ApplicationStatus.REJECTED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


# ---- Applications ----

@company_bp.route('/applications', methods=['GET'])
@role_required('COMPANY')
def list_applications():
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
        q = q.filter(PlacementDrive.status.in_([PlacementDriveStatus.CLOSED, PlacementDriveStatus.CANCELLED]))
    applications = q.order_by(Application.id.desc()).all()
    results = [application_to_dict(a, include_interviews=False) for a in applications]
    if search:
        results = [r for r in results if search.lower() in r['student_name'].lower()]
    return jsonify({'count': len(results), 'results': results})


@company_bp.route('/applications/<int:application_id>', methods=['GET'])
@role_required('COMPANY')
def get_application(application_id):
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    return jsonify(application_to_dict(application))


@company_bp.route('/applications/<int:application_id>/status', methods=['PATCH'])
@role_required('COMPANY')
def update_application_status(application_id):
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
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if application.status != ApplicationStatus.INTERVIEW:
        return error('Interviews can only be scheduled once the candidate reaches the Interview stage.')
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
        status=InterviewStatus.SCHEDULED,
    )
    db.session.add(interview)
    db.session.commit()
    return jsonify(interview_to_dict(interview)), 201


@company_bp.route('/applications/<int:application_id>/offer', methods=['POST'])
@role_required('COMPANY')
def make_offer(application_id):
    application = own_application_or_404(application_id)
    if not application:
        return error('Application not found.', 404)
    if application.status != ApplicationStatus.OFFER:
        return error('An offer can only be made once the candidate reaches the Offer stage.')

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
    db.session.commit()
    return jsonify(application_to_dict(application))


# ---- Interviews ----

@company_bp.route('/interviews', methods=['GET'])
@role_required('COMPANY')
def list_interviews():
    company = current_company()
    q = (InterviewSchedule.query
         .join(Application).join(PlacementDrive)
         .filter(PlacementDrive.company_id == company.id))
    drive_ids = [d for d in request.args.get('drive_ids', '').split(',') if d]
    if drive_ids:
        q = q.filter(Application.drive_id.in_([int(d) for d in drive_ids]))
    student_name = request.args.get('student_name', '').strip()
    order = InterviewSchedule.scheduled_date_time.desc() if request.args.get('sort') == 'newest' else InterviewSchedule.scheduled_date_time.asc()
    interviews = q.order_by(order).all()
    results = []
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
    return jsonify(company_to_dict(current_company()))


@company_bp.route('/profile', methods=['PATCH'])
@role_required('COMPANY')
def update_profile():
    company = current_company()
    data = request.get_json(force=True) or {}
    if 'name' in data and data['name'].strip():
        company.user.name = data['name'].strip()
    if 'company_name' in data and data['company_name'].strip():
        company.company_name = data['company_name'].strip()
    if 'hr_contact' in data:
        contact = data['hr_contact'].strip()
        if contact and not PHONE_RE.match(contact):
            return error('Please provide a valid HR contact number.')
        company.hr_contact = contact or None
    if 'industry' in data:
        company.industry = data['industry'].strip() or None
    if 'website' in data:
        company.website = data['website'].strip() or None
    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))
