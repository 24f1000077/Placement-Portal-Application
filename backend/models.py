from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from datetime import datetime, timezone
from enum import Enum

db = SQLAlchemy()
mail = Mail()


class Role(Enum):
    ADMIN = 'Admin'
    COMPANY = 'Company'
    STUDENT = 'Student'

class CompanyStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLACKLISTED = "blacklisted"

class StudentStatus(Enum):
    APPROVED = "approved"
    BLACKLISTED = "blacklisted"

class PlacementDriveStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLICATIONS_CLOSED = "applications_closed"
    CANCELLED = "cancelled"

class ApplicationStatus(Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    PLACED = "placed"
    WITHDRAWN = "withdrawn"

class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')


class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    students = db.relationship('StudentProfile', backref='branch_details', lazy=True)


class CompanyProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    hr_contact = db.Column(db.String(20), nullable=True)
    industry = db.Column(db.String(150))
    website = db.Column(db.String(255))
    approval_status = db.Column(db.Enum(CompanyStatus), default=CompanyStatus.PENDING)

    drives = db.relationship('PlacementDrive', backref='company', lazy=True, cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='company', lazy=True)


class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_number = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    approval_status = db.Column(db.Enum(StudentStatus), default=StudentStatus.APPROVED)
    cgpa = db.Column(db.Float, nullable=False)
    graduation_year = db.Column(db.Integer, nullable=False)
    resume = db.Column(db.LargeBinary, nullable=True)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text, nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)

    applications = db.relationship('Application', backref='student', lazy=True, cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='student', lazy=True)


# Many-to-many join table between placement drives and eligible branches.
drive_branches = db.Table('drive_branches',
    db.Column('drive_id', db.Integer, db.ForeignKey('placement_drive.id'), primary_key=True),
    db.Column('branch_id', db.Integer, db.ForeignKey('branch.id'), primary_key=True)
)


class PlacementDrive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text)
    location = db.Column(db.String(255))
    job_type = db.Column(db.String(50))
    application_deadline = db.Column(db.DateTime)
    cgpa = db.Column(db.Float, default=0.0)
    target_year = db.Column(db.Integer, nullable=True)
    skills_required = db.Column(db.Text)
    experience_required = db.Column(db.String(100))
    salary = db.Column(db.Float)
    benefits = db.Column(db.Text)
    notes = db.Column(db.Text)
    status = db.Column(db.Enum(PlacementDriveStatus), default=PlacementDriveStatus.PENDING)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    allowed_branches = db.relationship('Branch', secondary=drive_branches, lazy='subquery', backref=db.backref('allowed_drives', lazy=True))
    applications = db.relationship('Application', backref='drive', lazy=True, cascade='all, delete-orphan')
    placements = db.relationship('Placement', backref='drive', lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    feedback = db.Column(db.Text)
    offered_salary = db.Column(db.Float)
    offered_joining_date = db.Column(db.Date)
    offer_letter = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    interviews = db.relationship('InterviewSchedule', backref='application', lazy=True, cascade='all, delete-orphan')
    placement = db.relationship('Placement', backref='application', uselist=False, cascade='all, delete-orphan')

    __table_args__ = (db.UniqueConstraint('student_id', 'drive_id', name='_student_drive_uc'),)


class InterviewSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    scheduled_date_time = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(500))
    interviewer_name = db.Column(db.String(255))
    notes = db.Column(db.Text)
    feedback = db.Column(db.Text)
    status = db.Column(db.Enum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())


class Placement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profile.id'), nullable=False)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drive.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), unique=True, nullable=False)
    position = db.Column(db.String(255), nullable=False)
    salary_offered = db.Column(db.Float, nullable=False)
    joining_date = db.Column(db.Date)
    offer_letter = db.Column(db.LargeBinary)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())


class NotificationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_type = db.Column(db.String(100), nullable=False)
    recipient_email = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='pending')
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    error_message = db.Column(db.Text)
