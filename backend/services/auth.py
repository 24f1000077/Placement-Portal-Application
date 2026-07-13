import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Role, CompanyProfile, CompanyStatus, StudentProfile, StudentStatus, Branch
from serializers import student_to_dict, company_to_dict
from utils import error

auth_bp = Blueprint('auth', __name__)

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
PHONE_RE = re.compile(r'^\d{7,15}$')


def issue_token(user):
    claims = {'role': user.role.name, 'name': user.name, 'email': user.email}
    if user.role == Role.STUDENT:
        claims['profile_id'] = user.student_profile.id
    elif user.role == Role.COMPANY:
        claims['profile_id'] = user.company_profile.id
    return create_access_token(identity=str(user.id), additional_claims=claims)


@auth_bp.route('/branches', methods=['GET'])
def branches():
    rows = Branch.query.order_by(Branch.name).all()
    return jsonify([{'id': b.id, 'name': b.name} for b in rows])


@auth_bp.route('/register/student', methods=['POST'])
def register_student():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    contact_number = (data.get('contact_number') or '').strip()
    cgpa = data.get('cgpa')
    graduation_year = data.get('graduation_year')
    branch_id = data.get('branch_id')

    if not name or not email or not password or not contact_number:
        return error('Name, email, password and contact number are required.')
    if not EMAIL_RE.match(email):
        return error('Please provide a valid email address.')
    if len(password) < 6:
        return error('Password must be at least 6 characters long.')
    if not PHONE_RE.match(contact_number):
        return error('Please provide a valid contact number.')
    try:
        cgpa = float(cgpa)
    except (TypeError, ValueError):
        return error('CGPA must be a number.')
    if cgpa < 0 or cgpa > 10:
        return error('CGPA must be between 0.0 and 10.0.')
    try:
        graduation_year = int(graduation_year)
    except (TypeError, ValueError):
        return error('Graduation year must be a number.')
    if graduation_year < 2020 or graduation_year > 2035:
        return error('Graduation year must be between 2020 and 2035.')
    branch = Branch.query.get(branch_id)
    if not branch:
        return error('Please select a valid branch.')
    if User.query.filter_by(email=email).first():
        return error('An account with this email already exists.')

    user = User(name=name, role=Role.STUDENT, email=email, password=generate_password_hash(password))
    db.session.add(user)
    db.session.flush()

    profile = StudentProfile(
        user_id=user.id,
        contact_number=contact_number or None,
        approval_status=StudentStatus.APPROVED,
        cgpa=cgpa,
        graduation_year=graduation_year,
        branch_id=branch.id,
        skills=data.get('skills'),
        experience=data.get('experience'),
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify(message='Registration successful. You can now log in.'), 201


@auth_bp.route('/register/company', methods=['POST'])
def register_company():
    data = request.get_json(force=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    company_name = (data.get('company_name') or '').strip()
    hr_contact = (data.get('hr_contact') or '').strip()
    industry = (data.get('industry') or '').strip()
    website = (data.get('website') or '').strip()

    if not name or not email or not password or not company_name or not hr_contact:
        return error('Name, email, password, company name and HR contact number are required.')
    if not EMAIL_RE.match(email):
        return error('Please provide a valid email address.')
    if len(password) < 6:
        return error('Password must be at least 6 characters long.')
    if not PHONE_RE.match(hr_contact):
        return error('Please provide a valid HR contact number.')
    if User.query.filter_by(email=email).first():
        return error('An account with this email already exists.')

    user = User(name=name, role=Role.COMPANY, email=email, password=generate_password_hash(password))
    db.session.add(user)
    db.session.flush()

    profile = CompanyProfile(
        user_id=user.id,
        company_name=company_name,
        hr_contact=hr_contact or None,
        industry=industry or None,
        website=website or None,
        approval_status=CompanyStatus.PENDING,
    )
    db.session.add(profile)
    db.session.commit()

    return jsonify(message='Registration successful. Your account is pending admin approval.'), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        return error('Invalid email or password.', 401)
    if not user.is_active:
        return error('Your account has been deactivated. Please contact the placement cell.', 403)

    if user.role == Role.COMPANY:
        status = user.company_profile.approval_status
        if status == CompanyStatus.PENDING:
            return error('Your company registration is pending admin approval.', 403)
        if status == CompanyStatus.REJECTED:
            return error('Your company registration has been rejected.', 403)
        if status == CompanyStatus.BLACKLISTED:
            return error('Your company account has been blacklisted.', 403)

    if user.role == Role.STUDENT:
        if user.student_profile.approval_status == StudentStatus.BLACKLISTED:
            return error('Your student account has been blacklisted.', 403)

    token = issue_token(user)
    return jsonify(access_token=token, role=user.role.name, name=user.name, email=user.email)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    claims = get_jwt()
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return error('User not found.', 404)
    if not user.is_active:
        return error('Your account has been deactivated. Please contact the institute admin.', 401)
    payload = {'id': user.id, 'name': user.name, 'email': user.email, 'role': claims.get('role')}
    if user.role == Role.STUDENT:
        payload['profile'] = student_to_dict(user.student_profile)
    elif user.role == Role.COMPANY:
        payload['profile'] = company_to_dict(user.company_profile)
    return jsonify(payload)
