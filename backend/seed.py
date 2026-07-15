"""Seeds demo data across every role and status so the app can be explored end to end.

Run with: python seed.py
"""
from datetime import datetime, timedelta, date, timezone
from werkzeug.security import generate_password_hash

from app import create_app, seed_branches, seed_admin
from models import (
    db, User, Role, Branch,
    CompanyProfile, CompanyStatus,
    StudentProfile, StudentStatus,
    PlacementDrive, PlacementDriveStatus,
    Application, ApplicationStatus,
    InterviewSchedule, InterviewStatus,
    Placement,
)

app = create_app()

# A minimal, valid one-page PDF so seeded offer letters are actually downloadable/openable.
SAMPLE_OFFER_LETTER_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 150]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj
4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
5 0 obj<</Length 90>>
stream
BT /F1 14 Tf 20 100 Td (Offer Letter - Aarav Shah) Tj 0 -25 Td (Systems Engineer, Acme Corp) Tj ET
endstream
endobj
trailer<</Size 6/Root 1 0 R>>
%%EOF
"""


def make_user(name, email, password, role):
    # Returns the existing user for this email if one exists, otherwise creates it.
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(name=name, email=email, password=generate_password_hash(password), role=role, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def make_company(name, email, company_name, industry, website, status):
    # Creates (or reuses) the login user, then attaches a CompanyProfile with the given status.
    user = make_user(name, email, email.split('@')[0], Role.COMPANY)
    if user.company_profile:
        return user.company_profile
    profile = CompanyProfile(
        user_id=user.id, company_name=company_name, hr_contact='9876500000',
        industry=industry, website=website, approval_status=status,
    )
    # Mirrors production behavior: a blacklisted company's login is deactivated.
    if status == CompanyStatus.BLACKLISTED:
        user.is_active = False
    db.session.add(profile)
    db.session.flush()
    return profile


def make_student(name, email, branch_name, cgpa, grad_year, status, skills):
    # Creates (or reuses) the login user, then attaches a StudentProfile with the given status.
    user = make_user(name, email, email.split('@')[0], Role.STUDENT)
    if user.student_profile:
        return user.student_profile
    branch = Branch.query.filter_by(name=branch_name).first()
    profile = StudentProfile(
        user_id=user.id, contact_number='9800000000', approval_status=status,
        cgpa=cgpa, graduation_year=grad_year, branch_id=branch.id, skills=skills,
        experience='Built a few academic and personal projects.',
    )
    # Mirrors production behavior: a blacklisted student's login is deactivated.
    if status == StudentStatus.BLACKLISTED:
        user.is_active = False
    db.session.add(profile)
    db.session.flush()
    return profile


def make_drive(company, job_title, status, cgpa, target_year, branch_names, days_from_now, skills, salary, created_at=None):
    existing = PlacementDrive.query.filter_by(company_id=company.id, job_title=job_title).first()
    if existing:
        if created_at:
            existing.created_at = created_at
        return existing
    branches = Branch.query.filter(Branch.name.in_(branch_names)).all()
    drive = PlacementDrive(
        company_id=company.id, job_title=job_title, job_description=f'{job_title} role at {company.company_name}.',
        location='Bengaluru', job_type='Full-time',
        application_deadline=datetime.now(timezone.utc) + timedelta(days=days_from_now),
        cgpa=cgpa, min_target_year=target_year, max_target_year=target_year, skills_required=skills, salary=salary,
        status=status, allowed_branches=branches,
        created_at=created_at,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def make_application(student, drive, status, offered_salary=None, joining_date=None, offer_letter=None, created_at=None):
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing:
        if created_at:
            existing.created_at = created_at
        if offer_letter and not existing.offer_letter:
            existing.offer_letter = offer_letter
        return existing
    application = Application(
        student_id=student.id, drive_id=drive.id, status=status,
        offered_salary=offered_salary, offered_joining_date=joining_date, offer_letter=offer_letter,
        snapshot_cgpa=student.cgpa, snapshot_skills=student.skills,
        snapshot_experience=student.experience, snapshot_resume=student.resume,
        created_at=created_at,
    )
    db.session.add(application)
    db.session.flush()
    return application


def run():
    with app.app_context():
        # Creates tables and seeds branches/admin, same as a normal app startup.
        db.create_all()
        seed_branches()
        seed_admin()
        db.session.commit()

        acme = make_company('HR Priya', 'company1@placement.com', 'Acme Corp', 'Software', 'https://acme.example.com', CompanyStatus.APPROVED)
        beta = make_company('HR Rohan', 'company2@placement.com', 'Beta Inc', 'Finance', 'https://beta.example.com', CompanyStatus.APPROVED)
        make_company('HR Neha', 'company3@placement.com', 'Gamma Tech', 'Analytics', 'https://gamma.example.com', CompanyStatus.PENDING)
        make_company('HR Karan', 'company4@placement.com', 'Delta Systems', 'Hardware', 'https://delta.example.com', CompanyStatus.REJECTED)
        make_company('HR Simran', 'company5@placement.com', 'Epsilon Labs', 'Biotech', 'https://epsilon.example.com', CompanyStatus.BLACKLISTED)
        make_company('HR Ansh', 'company6@placement.com', 'A-Systems', 'IT', 'https://asystems.example.com', CompanyStatus.PENDING)
        make_company('HR Kaustubh', 'company7@placement.com', 'EdTech Foundation', 'IT', 'https://edtech.example.com', CompanyStatus.PENDING)
        db.session.commit()

        students = [
            make_student('Aarav Shah', 'student1@placement.com', 'Computer Science', 8.7, 2027, StudentStatus.APPROVED, 'Python, React, SQL'),
            make_student('Diya Mehta', 'student2@placement.com', 'Information Technology', 7.9, 2027, StudentStatus.APPROVED, 'Java, Spring, AWS'),
            make_student('Kabir Rao', 'student3@placement.com', 'Computer Science', 6.8, 2028, StudentStatus.APPROVED, 'C++, DSA'),
            make_student('Isha Nair', 'student4@placement.com', 'Electronics & Communication', 9.1, 2027, StudentStatus.APPROVED, 'Embedded C, VLSI'),
            make_student('Vivaan Gupta', 'student5@placement.com', 'Mechanical Engineering', 7.2, 2028, StudentStatus.APPROVED, 'AutoCAD, MATLAB'),
            make_student('Ananya Iyer', 'student6@placement.com', 'Computer Science', 8.3, 2026, StudentStatus.APPROVED, 'Python, ML, Pandas'),
            make_student('Reyansh Joshi', 'student7@placement.com', 'Electrical Engineering', 6.5, 2028, StudentStatus.APPROVED, 'Circuit Design'),
            make_student('Myra Verma', 'student8@placement.com', 'Information Technology', 8.9, 2027, StudentStatus.APPROVED, 'Vue, Node, MongoDB'),
            make_student('Arjun Desai', 'student9@placement.com', 'Civil Engineering', 7.5, 2028, StudentStatus.APPROVED, 'AutoCAD, Structural Design'),
            make_student('Sara Khan', 'student10@placement.com', 'Computer Science', 7.0, 2027, StudentStatus.BLACKLISTED, 'Python, Django'),
        ]
        db.session.commit()

        d_swe = make_drive(acme, 'Software Engineer', PlacementDriveStatus.APPROVED, 7.0, 2027, ['Computer Science', 'Information Technology'], 30, 'Python, React, SQL', 1200000)
        d_data = make_drive(acme, 'Data Analyst', PlacementDriveStatus.PENDING, 6.5, 2028, ['Computer Science'], 25, 'SQL, Excel', 900000)
        d_devops = make_drive(acme, 'DevOps Engineer', PlacementDriveStatus.APPLICATIONS_CLOSED, 7.5, 2027, ['Computer Science', 'Information Technology'], 10, 'Docker, AWS', 1100000)
        d_intern = make_drive(acme, 'Software Intern', PlacementDriveStatus.CANCELLED, 6.0, 2026, ['Computer Science'], 15, 'Python', 400000)
        d_backend = make_drive(acme, 'Backend Developer', PlacementDriveStatus.REJECTED, 7.0, 2027, ['Computer Science'], 20, 'Node.js', 1000000)
        d_pm = make_drive(beta, 'Product Manager', PlacementDriveStatus.APPROVED, 8.0, 2027, ['Computer Science', 'Information Technology', 'Electronics & Communication'], 40, 'Product Strategy', 1500000)
        d_qa = make_drive(beta, 'QA Engineer', PlacementDriveStatus.APPROVED, 6.0, 2028, ['Computer Science', 'Electrical Engineering'], 35, 'Selenium, Testing', 800000)
        d_frame = make_drive(acme, 'Framework Manager', PlacementDriveStatus.PENDING, 8.5, 2028, ['Computer Science'], 25, 'SQL, Excel', 900000)
        d_cloud = make_drive(acme, 'Cloud Solutions Architect', PlacementDriveStatus.PENDING, 8.5, 2028, ['Computer Science'], 25, 'AWS, Azure', 900000)


        # Drive to test send_daily_reminders (deadline in the next 48 hours)
        d_reminder = make_drive(acme, 'QA Automation Engineer', PlacementDriveStatus.APPROVED, 6.5, 2027, ['Computer Science', 'Information Technology'], 1.5, 'Python, Selenium', 950000)
        d_ineligible = make_drive(beta, 'Senior Hardware Engineer', PlacementDriveStatus.APPROVED, 7.0, 2027, ['Mechanical Engineering'], 30, 'AutoCAD', 1000000)
        db.session.commit()

        aarav, diya, kabir, isha, vivaan, ananya, reyansh, myra, arjun, sara = students

        # One application per ApplicationStatus value, spread across students and drives.
        make_application(aarav, d_swe, ApplicationStatus.APPLIED)
        make_application(diya, d_swe, ApplicationStatus.SHORTLISTED)
        app_interview = make_application(kabir, d_swe, ApplicationStatus.INTERVIEW)
        app_offer = make_application(myra, d_swe, ApplicationStatus.OFFER, offered_salary=1250000, joining_date=date.today() + timedelta(days=60))
        app_placed = make_application(ananya, d_pm, ApplicationStatus.PLACED, offered_salary=1500000, joining_date=date.today() + timedelta(days=45))
        make_application(reyansh, d_qa, ApplicationStatus.REJECTED)
        make_application(vivaan, d_devops, ApplicationStatus.WITHDRAWN)
        make_application(isha, d_pm, ApplicationStatus.APPLIED)
        make_application(arjun, d_qa, ApplicationStatus.SHORTLISTED)
        db.session.commit()

        # Schedules an upcoming interview for the INTERVIEW-stage application.
        if not app_interview.interviews:
            db.session.add(InterviewSchedule(
                application_id=app_interview.id,
                scheduled_date_time=datetime.now(timezone.utc) + timedelta(days=3),
                interviewer_name='Priya Sharma', meeting_link='https://meet.example.com/swe-interview',
                status=InterviewStatus.SCHEDULED,
            ))

        # June 2026 data to test the generate_monthly_report Celery task
        d_june_swe = make_drive(
            acme, 'June Systems Engineer', PlacementDriveStatus.APPROVED, 7.0, 2027,
            ['Computer Science', 'Information Technology'], 30, 'C, Unix, SQL', 1300000,
            created_at=datetime(2026, 6, 10, 10, 0, 0)
        )
        app_june1 = make_application(
            aarav, d_june_swe, ApplicationStatus.PLACED, offered_salary=1300000, joining_date=date(2026, 8, 1),
            offer_letter=SAMPLE_OFFER_LETTER_PDF, created_at=datetime(2026, 6, 12, 14, 0, 0),
        )
        app_june2 = make_application(diya, d_june_swe, ApplicationStatus.REJECTED, created_at=datetime(2026, 6, 13, 11, 0, 0))

        if not app_placed.placement:
            db.session.add(Placement(
                student_id=ananya.id, company_id=beta.id, drive_id=d_pm.id, application_id=app_placed.id,
                position=d_pm.job_title, salary_offered=app_placed.offered_salary, joining_date=app_placed.offered_joining_date,
            ))
        if not app_june1.placement:
            db.session.add(Placement(
                student_id=aarav.id, company_id=acme.id, drive_id=d_june_swe.id, application_id=app_june1.id,
                position=d_june_swe.job_title, salary_offered=app_june1.offered_salary, joining_date=app_june1.offered_joining_date,
                created_at=datetime(2026, 6, 25, 16, 0, 0)
            ))
        db.session.commit()
        print('Seed data created successfully.')


if __name__ == '__main__':
    run()
