import re
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, send_file
import io

from flask_jwt_extended import get_jwt_identity

from models import (
    db, User, StudentProfile,
    PlacementDrive, PlacementDriveStatus,
    Application, ApplicationStatus,
    Placement,
)
from serializers import student_to_dict, drive_to_dict, application_to_dict
from utils import role_required, error
from app import cache

student_bp = Blueprint('student', __name__)

PHONE_RE = re.compile(r'^\d{7,15}$')
ACTIVE_STATUSES = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER]


def current_student():
    user = User.query.get(int(get_jwt_identity()))
    return user.student_profile


def is_eligible(student, drive):
    if drive.allowed_branches and student.branch_id not in [b.id for b in drive.allowed_branches]:
        return False
    if drive.target_year and student.graduation_year != drive.target_year:
        return False
    if drive.cgpa and student.cgpa < drive.cgpa:
        return False
    return True


# ---- Placement Drives ----

@student_bp.route('/drives', methods=['GET'])
@role_required('STUDENT')
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
        eligible = is_eligible(student, drive)
        if eligible_only and not eligible:
            continue
        deadline_passed = bool(drive.application_deadline and drive.application_deadline <= datetime.now(timezone.utc).replace(tzinfo=drive.application_deadline.tzinfo))
        payload = drive_to_dict(drive, include_applicant_count=False)
        payload['eligible'] = eligible
        payload['already_applied'] = drive.id in applied_drive_ids
        payload['deadline_passed'] = deadline_passed
        results.append(payload)
    return jsonify({'count': len(results), 'results': results})


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
    applications = q.order_by(Application.id.desc()).all()
    return jsonify({'count': len(applications), 'results': [application_to_dict(a, include_interviews=False) for a in applications]})


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


@student_bp.route('/applications/<int:application_id>/reject-offer', methods=['POST'])
@role_required('STUDENT')
def reject_offer(application_id):
    student = current_student()
    application = Application.query.filter_by(id=application_id, student_id=student.id).first_or_404()
    if application.status != ApplicationStatus.OFFER:
        return error('Only applications in the Offer stage can be rejected.')
    application.status = ApplicationStatus.REJECTED
    db.session.commit()
    return jsonify(application_to_dict(application))


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
    if 'skills' in data:
        student.skills = data['skills']
    if 'experience' in data:
        student.experience = data['experience']
    if resume_file:
        student.resume = resume_file.read()

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
