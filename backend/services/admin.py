import re
import io
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify, send_file

from models import (
    db, User, Role, Branch,
    CompanyProfile, CompanyStatus,
    StudentProfile, StudentStatus,
    PlacementDrive, PlacementDriveStatus, drive_branches,
    Application, ApplicationStatus,
    InterviewSchedule, InterviewStatus, Placement,
)
from serializers import company_to_dict, student_to_dict, drive_to_dict, application_to_dict, interview_to_dict
from utils import role_required, error
from app import cache

admin_bp = Blueprint('admin', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
ACTIVE_APPLICATION_STATUSES = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER]


def split_param(name):
    raw = request.args.get(name, '')
    return [v for v in raw.split(',') if v]


@admin_bp.route('/overview', methods=['GET'])
@role_required('ADMIN')
def overview():
    return jsonify({
        'total_students': StudentProfile.query.count(),
        'total_companies_approved': CompanyProfile.query.filter_by(approval_status=CompanyStatus.APPROVED).count(),
        'total_drives_approved': PlacementDrive.query.filter_by(status=PlacementDriveStatus.APPROVED).count(),
    })


# ---- Companies ----

@admin_bp.route('/companies', methods=['GET'])
@role_required('ADMIN')
@cache.cached(timeout=60, query_string=True)
def list_companies():
    q = CompanyProfile.query.join(User)
    search = request.args.get('search', '').strip()
    if search:
        q = q.filter(CompanyProfile.company_name.ilike(f'%{search}%'))
    statuses = split_param('status')
    if statuses:
        q = q.filter(CompanyProfile.approval_status.in_([CompanyStatus[s] for s in statuses if s in CompanyStatus.__members__]))
    companies = q.order_by(CompanyProfile.id.desc()).all()
    return jsonify({'count': len(companies), 'results': [company_to_dict(c) for c in companies]})


@admin_bp.route('/companies/<int:company_id>', methods=['PATCH'])
@role_required('ADMIN')
def update_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    data = request.get_json(force=True) or {}

    if 'name' in data and data['name'].strip():
        company.user.name = data['name'].strip()
    if 'email' in data and data['email'].strip():
        email = data['email'].strip().lower()
        if not EMAIL_RE.match(email):
            return error('Please provide a valid email address.')
        existing = User.query.filter(User.email == email, User.id != company.user_id).first()
        if existing:
            return error('An account with this email already exists.')
        company.user.email = email
    if 'company_name' in data:
        if not data['company_name'].strip():
            return error('Company name cannot be empty.')
        company.company_name = data['company_name'].strip()
    if 'hr_contact' in data:
        company.hr_contact = data['hr_contact'].strip() or None
    if 'industry' in data:
        company.industry = data['industry'].strip() or None
    if 'website' in data:
        company.website = data['website'].strip() or None

    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))


@admin_bp.route('/companies/<int:company_id>/approve', methods=['POST'])
@role_required('ADMIN')
def approve_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    if company.approval_status != CompanyStatus.PENDING:
        return error('Only pending companies can be approved.')
    company.approval_status = CompanyStatus.APPROVED
    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))


@admin_bp.route('/companies/<int:company_id>/reject', methods=['POST'])
@role_required('ADMIN')
def reject_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    if company.approval_status != CompanyStatus.PENDING:
        return error('Only pending companies can be rejected.')
    company.approval_status = CompanyStatus.REJECTED
    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))


@admin_bp.route('/companies/<int:company_id>/blacklist', methods=['POST'])
@role_required('ADMIN')
def blacklist_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    if company.approval_status != CompanyStatus.APPROVED:
        return error('Only approved companies can be blacklisted.')
    company.approval_status = CompanyStatus.BLACKLISTED
    company.user.is_active = False
    for drive in company.drives:
        if drive.status not in (PlacementDriveStatus.CANCELLED, PlacementDriveStatus.APPLICATIONS_CLOSED):
            drive.status = PlacementDriveStatus.CANCELLED
        for application in drive.applications:
            if application.status != ApplicationStatus.PLACED:
                application.status = ApplicationStatus.REJECTED
                application.feedback = 'Automatically rejected: the company was blacklisted.'
    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))


@admin_bp.route('/companies/<int:company_id>/whitelist', methods=['POST'])
@role_required('ADMIN')
def whitelist_company(company_id):
    company = CompanyProfile.query.get_or_404(company_id)
    if company.approval_status != CompanyStatus.BLACKLISTED:
        return error('Only blacklisted companies can be whitelisted.')
    company.approval_status = CompanyStatus.APPROVED
    company.user.is_active = True
    db.session.commit()
    cache.clear()
    return jsonify(company_to_dict(company))


# ---- Placement Drives ----

@admin_bp.route('/drives', methods=['GET'])
@role_required('ADMIN')
@cache.cached(timeout=60, query_string=True)
def list_drives():
    q = PlacementDrive.query.join(CompanyProfile)
    search = request.args.get('search', '').strip()
    if search:
        q = q.filter(PlacementDrive.job_title.ilike(f'%{search}%'))
    company_ids = split_param('company_ids')
    if company_ids:
        q = q.filter(PlacementDrive.company_id.in_([int(c) for c in company_ids]))
    statuses = split_param('status')
    if statuses:
        q = q.filter(PlacementDrive.status.in_([PlacementDriveStatus[s] for s in statuses if s in PlacementDriveStatus.__members__]))
    skills = request.args.get('skills', '').strip()
    if skills:
        q = q.filter(PlacementDrive.skills_required.ilike(f'%{skills}%'))
    min_cgpa = request.args.get('min_cgpa')
    if min_cgpa:
        q = q.filter(PlacementDrive.cgpa >= float(min_cgpa))
    branches = split_param('branches')
    if branches:
        q = q.join(drive_branches).join(Branch).filter(Branch.name.in_(branches))
    deadline_from = request.args.get('deadline_from')
    if deadline_from:
        q = q.filter(PlacementDrive.application_deadline >= datetime.fromisoformat(deadline_from))
    deadline_to = request.args.get('deadline_to')
    if deadline_to:
        q = q.filter(PlacementDrive.application_deadline < datetime.fromisoformat(deadline_to) + timedelta(days=1))
    drives = q.order_by(PlacementDrive.id.desc()).all()
    return jsonify({'count': len(drives), 'results': [drive_to_dict(d) for d in drives]})


@admin_bp.route('/drives/<int:drive_id>', methods=['PATCH'])
@role_required('ADMIN')
def update_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    data = request.get_json(force=True) or {}

    for field in ['job_title', 'job_description', 'location', 'job_type',
                  'skills_required', 'experience_required', 'benefits', 'notes']:
        if field in data:
            setattr(drive, field, data[field])
    if 'cgpa' in data:
        try:
            cgpa = float(data['cgpa'])
        except (TypeError, ValueError):
            return error('Minimum CGPA must be a number.')
        if cgpa < 0 or cgpa > 10:
            return error('Minimum CGPA must be between 0.0 and 10.0.')
        drive.cgpa = cgpa
    if 'salary' in data:
        try:
            salary = float(data['salary'])
        except (TypeError, ValueError):
            return error('Salary must be a number.')
        if salary <= 0:
            return error('Salary must be a positive number.')
        drive.salary = salary
    if 'target_year' in data:
        drive.target_year = int(data['target_year'])
    if 'application_deadline' in data:
        drive.application_deadline = datetime.fromisoformat(data['application_deadline'])
    if 'branch_ids' in data:
        drive.allowed_branches = Branch.query.filter(Branch.id.in_(data['branch_ids'])).all()

    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@admin_bp.route('/drives/<int:drive_id>/approve', methods=['POST'])
@role_required('ADMIN')
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != PlacementDriveStatus.PENDING:
        return error('Only pending drives can be approved.')
    drive.status = PlacementDriveStatus.APPROVED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@admin_bp.route('/drives/<int:drive_id>/reject', methods=['POST'])
@role_required('ADMIN')
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != PlacementDriveStatus.PENDING:
        return error('Only pending drives can be rejected.')
    drive.status = PlacementDriveStatus.REJECTED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@admin_bp.route('/drives/<int:drive_id>/close', methods=['POST'])
@role_required('ADMIN')
def close_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be closed.')
    drive.status = PlacementDriveStatus.APPLICATIONS_CLOSED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@admin_bp.route('/drives/<int:drive_id>/cancel', methods=['POST'])
@role_required('ADMIN')
def cancel_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('Only approved drives can be cancelled.')
    drive.status = PlacementDriveStatus.CANCELLED
    for application in drive.applications:
        if application.status in ACTIVE_APPLICATION_STATUSES:
            application.status = ApplicationStatus.REJECTED
            application.feedback = 'Automatically rejected: the placement drive was cancelled.'
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


@admin_bp.route('/drives/<int:drive_id>/extend-deadline', methods=['POST'])
@role_required('ADMIN')
def extend_deadline(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status not in (PlacementDriveStatus.APPROVED, PlacementDriveStatus.APPLICATIONS_CLOSED):
        return error('Only approved or applications-closed drives can have their deadline extended.')
    data = request.get_json(force=True) or {}
    try:
        new_deadline = datetime.fromisoformat(data.get('application_deadline', ''))
    except ValueError:
        return error('Please provide a valid deadline date.')
    if new_deadline <= datetime.now(timezone.utc).replace(tzinfo=new_deadline.tzinfo):
        return error('The new deadline must be a future date.')
    drive.application_deadline = new_deadline
    if drive.status == PlacementDriveStatus.APPLICATIONS_CLOSED:
        drive.status = PlacementDriveStatus.APPROVED
    db.session.commit()
    cache.clear()
    return jsonify(drive_to_dict(drive))


# ---- Applications ----

@admin_bp.route('/applications', methods=['GET'])
@role_required('ADMIN')
def list_applications():
    q = Application.query.join(StudentProfile).join(PlacementDrive).join(CompanyProfile)
    search = request.args.get('search', '').strip()
    if search:
        q = q.join(User, StudentProfile.user_id == User.id).filter(User.name.ilike(f'%{search}%'))
    company_ids = split_param('company_ids')
    if company_ids:
        q = q.filter(PlacementDrive.company_id.in_([int(c) for c in company_ids]))
    drive_ids = split_param('drive_ids')
    if drive_ids:
        q = q.filter(Application.drive_id.in_([int(d) for d in drive_ids]))
    statuses = split_param('status')
    if statuses:
        q = q.filter(Application.status.in_([ApplicationStatus[s] for s in statuses if s in ApplicationStatus.__members__]))
    applications = q.order_by(Application.id.desc()).all()
    return jsonify({'count': len(applications), 'results': [application_to_dict(a, include_interviews=False) for a in applications]})


@admin_bp.route('/applications/<int:application_id>', methods=['GET'])
@role_required('ADMIN')
def get_application(application_id):
    application = Application.query.get_or_404(application_id)
    return jsonify(application_to_dict(application))


@admin_bp.route('/applications/<int:application_id>', methods=['PATCH'])
@role_required('ADMIN')
def update_application(application_id):
    application = Application.query.get_or_404(application_id)
    data = request.get_json(force=True) or {}

    if 'status' in data:
        if data['status'] not in ApplicationStatus.__members__:
            return error('Invalid application status.')
        application.status = ApplicationStatus[data['status']]
    if 'feedback' in data:
        application.feedback = data['feedback'] or None
    if 'offered_salary' in data:
        try:
            application.offered_salary = float(data['offered_salary']) if data['offered_salary'] not in (None, '') else None
        except (TypeError, ValueError):
            return error('Offered salary must be a number.')
    if 'offered_joining_date' in data:
        try:
            application.offered_joining_date = (
                datetime.fromisoformat(data['offered_joining_date']).date() if data['offered_joining_date'] else None
            )
        except ValueError:
            return error('Offered joining date must be a valid date.')

    db.session.commit()
    cache.clear()
    return jsonify(application_to_dict(application))


# ---- Students ----

@admin_bp.route('/students', methods=['GET'])
@role_required('ADMIN')
@cache.cached(timeout=60, query_string=True)
def list_students():
    q = StudentProfile.query.join(User)
    search = request.args.get('search', '').strip()
    if search:
        q = q.filter(db.or_(User.name.ilike(f'%{search}%'), User.email.ilike(f'%{search}%')))
    branches = split_param('branches')
    if branches:
        q = q.join(Branch, StudentProfile.branch_id == Branch.id).filter(Branch.name.in_(branches))
    grad_years = split_param('graduation_years')
    if grad_years:
        q = q.filter(StudentProfile.graduation_year.in_([int(y) for y in grad_years]))
    min_cgpa = request.args.get('min_cgpa')
    if min_cgpa:
        q = q.filter(StudentProfile.cgpa >= float(min_cgpa))
    max_cgpa = request.args.get('max_cgpa')
    if max_cgpa:
        q = q.filter(StudentProfile.cgpa <= float(max_cgpa))
    placement_status = request.args.get('placement_status', '').strip().upper()
    if placement_status == 'PLACED':
        q = q.filter(StudentProfile.placements.any())
    elif placement_status == 'UNPLACED':
        q = q.filter(~StudentProfile.placements.any())
    students = q.order_by(StudentProfile.id.desc()).all()
    return jsonify({'count': len(students), 'results': [student_to_dict(s) for s in students]})


@admin_bp.route('/students/<int:student_id>', methods=['PATCH'])
@role_required('ADMIN')
def update_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    data = request.get_json(force=True) or {}

    if 'name' in data and data['name'].strip():
        student.user.name = data['name'].strip()
    if 'email' in data and data['email'].strip():
        email = data['email'].strip().lower()
        if not EMAIL_RE.match(email):
            return error('Please provide a valid email address.')
        existing = User.query.filter(User.email == email, User.id != student.user_id).first()
        if existing:
            return error('An account with this email already exists.')
        student.user.email = email
    if 'contact_number' in data:
        student.contact_number = data['contact_number'].strip() or None
    if 'cgpa' in data:
        try:
            cgpa = float(data['cgpa'])
        except (TypeError, ValueError):
            return error('CGPA must be a number.')
        if cgpa < 0 or cgpa > 10:
            return error('CGPA must be between 0.0 and 10.0.')
        student.cgpa = cgpa
    if 'graduation_year' in data:
        student.graduation_year = int(data['graduation_year'])
    if 'branch_id' in data:
        branch = Branch.query.get(data['branch_id'])
        if not branch:
            return error('Please select a valid branch.')
        student.branch_id = branch.id
    if 'skills' in data:
        student.skills = data['skills']
    if 'experience' in data:
        student.experience = data['experience']

    db.session.commit()
    cache.clear()
    return jsonify(student_to_dict(student))


@admin_bp.route('/students/<int:student_id>/blacklist', methods=['POST'])
@role_required('ADMIN')
def blacklist_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    if student.approval_status != StudentStatus.APPROVED:
        return error('Only active students can be blacklisted.')
    student.approval_status = StudentStatus.BLACKLISTED
    student.user.is_active = False
    for application in student.applications:
        if application.status in ACTIVE_APPLICATION_STATUSES:
            application.status = ApplicationStatus.WITHDRAWN
    db.session.commit()
    cache.clear()
    return jsonify(student_to_dict(student))


@admin_bp.route('/students/<int:student_id>/whitelist', methods=['POST'])
@role_required('ADMIN')
def whitelist_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    if student.approval_status != StudentStatus.BLACKLISTED:
        return error('Only blacklisted students can be whitelisted.')
    student.approval_status = StudentStatus.APPROVED
    student.user.is_active = True
    db.session.commit()
    cache.clear()
    return jsonify(student_to_dict(student))


@admin_bp.route('/students/<int:student_id>/resume', methods=['GET'])
@role_required('ADMIN')
def download_student_resume(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    if not student.resume:
        return error('No resume uploaded yet.', 404)
    return send_file(io.BytesIO(student.resume), mimetype='application/pdf', download_name='resume.pdf')


@admin_bp.route('/applications/<int:application_id>/resume', methods=['GET'])
@role_required('ADMIN')
def download_application_resume(application_id):
    application = Application.query.get_or_404(application_id)
    if not application.student.resume:
        return error('No resume uploaded yet.', 404)
    return send_file(io.BytesIO(application.student.resume), mimetype='application/pdf', download_name='resume.pdf')


@admin_bp.route('/applications/<int:application_id>/offer-letter', methods=['GET'])
@role_required('ADMIN')
def download_application_offer_letter(application_id):
    application = Application.query.get_or_404(application_id)
    if not application.offer_letter:
        return error('No offer letter uploaded yet.', 404)
    return send_file(io.BytesIO(application.offer_letter), mimetype='application/pdf', download_name='offer_letter.pdf')


# ---- Interviews ----

@admin_bp.route('/interviews', methods=['GET'])
@role_required('ADMIN')
def list_interviews():
    q = (InterviewSchedule.query
         .join(Application).join(StudentProfile).join(User, StudentProfile.user_id == User.id)
         .join(PlacementDrive).join(CompanyProfile))
    drive_or_company = request.args.get('search_drive_company', '').strip()
    if drive_or_company:
        q = q.filter(db.or_(
            PlacementDrive.job_title.ilike(f'%{drive_or_company}%'),
            CompanyProfile.company_name.ilike(f'%{drive_or_company}%'),
        ))
    student_name = request.args.get('student_name', '').strip()
    if student_name:
        q = q.filter(User.name.ilike(f'%{student_name}%'))
    order = InterviewSchedule.scheduled_date_time.desc() if request.args.get('sort') == 'newest' else InterviewSchedule.scheduled_date_time.asc()
    interviews = q.order_by(order).all()
    results = []
    for interview in interviews:
        application = interview.application
        payload = interview_to_dict(interview)
        payload.update({
            'student_name': application.student.user.name,
            'job_title': application.drive.job_title,
            'company_name': application.drive.company.company_name,
        })
        results.append(payload)
    return jsonify({'count': len(results), 'results': results})


@admin_bp.route('/interviews/<int:interview_id>', methods=['PATCH'])
@role_required('ADMIN')
def update_interview(interview_id):
    interview = InterviewSchedule.query.get_or_404(interview_id)
    data = request.get_json(force=True) or {}

    if 'scheduled_date_time' in data:
        try:
            interview.scheduled_date_time = datetime.fromisoformat(data['scheduled_date_time'])
        except (TypeError, ValueError):
            return error('Scheduled date/time must be a valid datetime.')
    if 'meeting_link' in data:
        interview.meeting_link = data['meeting_link'] or None
    if 'interviewer_name' in data:
        interview.interviewer_name = data['interviewer_name'] or None
    if 'notes' in data:
        interview.notes = data['notes'] or None
    if 'feedback' in data:
        interview.feedback = data['feedback'] or None
    if 'status' in data:
        if data['status'] not in InterviewStatus.__members__:
            return error('Invalid interview status.')
        interview.status = InterviewStatus[data['status']]

    db.session.commit()
    cache.clear()
    return jsonify(interview_to_dict(interview))
