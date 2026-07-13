import re
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
import io

from celery import Celery
from celery.result import AsyncResult
from flask_jwt_extended import get_jwt_identity

import config
from models import (
    db, User, StudentProfile, CompanyProfile,
    PlacementDrive, PlacementDriveStatus,
    Application, ApplicationStatus,
    Placement,
)
from serializers import student_to_dict, drive_to_dict, application_to_dict
from utils import role_required, error, apply_password_change
from app import cache

student_bp = Blueprint('student', __name__)

# Lightweight client used only to enqueue/poll tasks; the worker process (celery_workers.py) owns execution.
task_client = Celery(broker=config.CELERY_BROKER_URL, backend=config.CELERY_RESULT_BACKEND)

PHONE_RE = re.compile(r'^\d{7,15}$')
ACTIVE_STATUSES = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER]


def current_student():
    user = User.query.get(int(get_jwt_identity()))
    return user.student_profile


def ineligibility_reasons(student, drive):
    reasons = []
    if drive.allowed_branches and student.branch_id not in [b.id for b in drive.allowed_branches]:
        reasons.append(f'This drive is open to {", ".join(b.name for b in drive.allowed_branches)} only.')
    if drive.target_year and student.graduation_year != drive.target_year:
        reasons.append(f'This drive targets the {drive.target_year} graduating batch; you are graduating in {student.graduation_year}.')
    if drive.cgpa and student.cgpa < drive.cgpa:
        reasons.append(f'This drive requires a minimum CGPA of {drive.cgpa}; your CGPA is {student.cgpa}.')
    return reasons


def is_eligible(student, drive):
    return not ineligibility_reasons(student, drive)


# ---- Placement Drives ----

def drives_cache_key():
    return f'student-drives:{get_jwt_identity()}:{request.query_string.decode()}'


@student_bp.route('/drives', methods=['GET'])
@role_required('STUDENT')
@cache.cached(timeout=60, key_prefix=drives_cache_key)
def list_drives():
    student = current_student()
    q = PlacementDrive.query.filter_by(status=PlacementDriveStatus.APPROVED)
    search = request.args.get('search', '').strip()
    if search:
        q = q.filter(db.or_(
            PlacementDrive.job_title.ilike(f'%{search}%'),
            PlacementDrive.job_description.ilike(f'%{search}%'),
        ))
    company_ids = [c for c in request.args.get('company_ids', '').split(',') if c]
    if company_ids:
        q = q.filter(PlacementDrive.company_id.in_([int(c) for c in company_ids]))
    skills = request.args.get('skills', '').strip()
    if skills:
        q = q.filter(PlacementDrive.skills_required.ilike(f'%{skills}%'))

    applied_drive_ids = {a.drive_id for a in student.applications}
    eligible_only = request.args.get('eligible_only') == 'true'

    results = []
    for drive in q.order_by(PlacementDrive.created_at.desc()).all():
        reasons = ineligibility_reasons(student, drive)
        if eligible_only and reasons:
            continue
        deadline_passed = bool(drive.application_deadline and drive.application_deadline <= datetime.now(timezone.utc).replace(tzinfo=drive.application_deadline.tzinfo))
        payload = drive_to_dict(drive, include_applicant_count=False)
        payload['eligible'] = not reasons
        payload['ineligibility_reasons'] = reasons
        payload['already_applied'] = drive.id in applied_drive_ids
        payload['deadline_passed'] = deadline_passed
        results.append(payload)
    return jsonify({'count': len(results), 'results': results})


@student_bp.route('/companies', methods=['GET'])
@role_required('STUDENT')
def list_companies_with_drives():
    companies = (CompanyProfile.query
                 .join(PlacementDrive, PlacementDrive.company_id == CompanyProfile.id)
                 .filter(PlacementDrive.status == PlacementDriveStatus.APPROVED)
                 .distinct().order_by(CompanyProfile.company_name).all())
    return jsonify([{'id': c.id, 'name': c.company_name} for c in companies])


@student_bp.route('/drives/<int:drive_id>/apply', methods=['POST'])
@role_required('STUDENT')
def apply_to_drive(drive_id):
    student = current_student()
    drive = PlacementDrive.query.get_or_404(drive_id)
    if drive.status != PlacementDriveStatus.APPROVED:
        return error('This drive is not currently accepting applications.')
    if drive.application_deadline and drive.application_deadline <= datetime.now(timezone.utc).replace(tzinfo=drive.application_deadline.tzinfo):
        return error('The application deadline for this drive has passed.')
    if not is_eligible(student, drive):
        return error('You do not meet the eligibility criteria for this drive.')
    if Application.query.filter_by(student_id=student.id, drive_id=drive.id).first():
        return error('You have already applied to this drive.', 409)

    application = Application(student_id=student.id, drive_id=drive.id, status=ApplicationStatus.APPLIED)
    db.session.add(application)
    db.session.commit()
    cache.clear()
    return jsonify(application_to_dict(application)), 201


# ---- Applications ----

@student_bp.route('/applications', methods=['GET'])
@role_required('STUDENT')
def list_applications():
    student = current_student()
    q = Application.query.filter_by(student_id=student.id)
    statuses = [s for s in request.args.get('status', '').split(',') if s]
    if statuses:
        q = q.filter(Application.status.in_([ApplicationStatus[s] for s in statuses if s in ApplicationStatus.__members__]))
    applications = q.order_by(Application.application_date.desc()).all()
    results = [application_to_dict(a, include_interviews=False) for a in applications]
    search = request.args.get('search', '').strip().lower()
    if search:
        results = [r for r in results if search in r['company_name'].lower() or search in r['job_title'].lower()]
    return jsonify({'count': len(results), 'results': results})


@student_bp.route('/applications/<int:application_id>', methods=['GET'])
@role_required('STUDENT')
def get_application(application_id):
    student = current_student()
    application = Application.query.filter_by(id=application_id, student_id=student.id).first_or_404()
    return jsonify(application_to_dict(application))


@student_bp.route('/applications/<int:application_id>/withdraw', methods=['POST'])
@role_required('STUDENT')
def withdraw_application(application_id):
    student = current_student()
    application = Application.query.filter_by(id=application_id, student_id=student.id).first_or_404()
    if application.status not in ACTIVE_STATUSES:
        return error('Only active applications can be withdrawn.')
    application.status = ApplicationStatus.WITHDRAWN
    db.session.commit()
    return jsonify(application_to_dict(application))


@student_bp.route('/applications/<int:application_id>/accept-offer', methods=['POST'])
@role_required('STUDENT')
def accept_offer(application_id):
    student = current_student()
    application = Application.query.filter_by(id=application_id, student_id=student.id).first_or_404()
    if application.status != ApplicationStatus.OFFER:
        return error('Only applications in the Offer stage can be accepted.')

    placement = Placement(
        student_id=student.id,
        company_id=application.drive.company_id,
        drive_id=application.drive_id,
        application_id=application.id,
        position=application.drive.job_title,
        salary_offered=application.offered_salary,
        joining_date=application.offered_joining_date,
        offer_letter=application.offer_letter,
    )
    application.status = ApplicationStatus.PLACED
    db.session.add(placement)
    db.session.commit()
    return jsonify(application_to_dict(application))


@student_bp.route('/applications/<int:application_id>/offer-letter', methods=['GET'])
@role_required('STUDENT')
def download_offer_letter(application_id):
    student = current_student()
    application = Application.query.filter_by(id=application_id, student_id=student.id).first_or_404()
    if not application.offer_letter:
        return error('No offer letter uploaded yet.', 404)
    return send_file(io.BytesIO(application.offer_letter), mimetype='application/pdf', download_name='offer_letter.pdf')


# ---- Profile ----

@student_bp.route('/profile', methods=['GET'])
@role_required('STUDENT')
def get_profile():
    return jsonify(student_to_dict(current_student()))


@student_bp.route('/profile', methods=['PATCH'])
@role_required('STUDENT')
def update_profile():
    student = current_student()
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
        resume_file = request.files.get('resume')
    else:
        data = request.get_json(force=True) or {}
        resume_file = None

    if 'name' in data and data['name'].strip():
        student.user.name = data['name'].strip()
    if 'contact_number' in data:
        contact = data['contact_number'].strip()
        if contact and not PHONE_RE.match(contact):
            return error('Please provide a valid contact number.')
        student.contact_number = contact or None
    if 'cgpa' in data:
        try:
            cgpa = float(data['cgpa'])
        except (TypeError, ValueError):
            return error('CGPA must be a number.')
        if cgpa < 0 or cgpa > 10:
            return error('CGPA must be between 0.0 and 10.0.')
        student.cgpa = cgpa
    if 'skills' in data:
        student.skills = data['skills']
    if 'experience' in data:
        student.experience = data['experience']
    if resume_file:
        student.resume = resume_file.read()

    password_error = apply_password_change(student.user, data)
    if password_error:
        return password_error

    db.session.commit()
    cache.clear()
    return jsonify(student_to_dict(student))


@student_bp.route('/profile/resume', methods=['GET'])
@role_required('STUDENT')
def download_resume():
    student = current_student()
    if not student.resume:
        return error('No resume uploaded yet.', 404)
    return send_file(io.BytesIO(student.resume), mimetype='application/pdf', download_name='resume.pdf')


# ---- Async CSV export ----

FINISHED_STATUSES = [ApplicationStatus.REJECTED.name, ApplicationStatus.WITHDRAWN.name, ApplicationStatus.PLACED.name]


@student_bp.route('/applications/export', methods=['POST'])
@role_required('STUDENT')
def export_applications():
    student = current_student()
    statuses = FINISHED_STATUSES if request.args.get('history') == 'true' else None
    task = task_client.send_task('tasks.export_applications_csv', args=[student.id, statuses])
    return jsonify({'task_id': task.id}), 202


@student_bp.route('/applications/export/<task_id>', methods=['GET'])
@role_required('STUDENT')
def export_status(task_id):
    result = AsyncResult(task_id, app=task_client)
    return jsonify({'state': result.state, 'ready': result.ready()})


@student_bp.route('/applications/export/<task_id>/download', methods=['GET'])
@role_required('STUDENT')
def export_download(task_id):
    result = AsyncResult(task_id, app=task_client)
    if not result.ready():
        return error('Export is not ready yet.', 409)
    payload = result.result
    return send_file(
        io.BytesIO(payload['csv'].encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=payload['filename'],
    )
