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


def make_user(name, email, password, role):
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(name=name, email=email, password=generate_password_hash(password), role=role, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def make_company(name, email, company_name, industry, website, status):
    user = make_user(name, email, email.split('@')[0], Role.COMPANY)
    if user.company_profile:
        return user.company_profile
    profile = CompanyProfile(
        user_id=user.id, company_name=company_name, hr_contact='9876500000',
        industry=industry, website=website, approval_status=status,
    )
    if status == CompanyStatus.BLACKLISTED:
        user.is_active = False
    db.session.add(profile)
    db.session.flush()
    return profile


def make_student(name, email, branch_name, cgpa, grad_year, status, skills):
    user = make_user(name, email, email.split('@')[0], Role.STUDENT)
    if user.student_profile:
        return user.student_profile
    branch = Branch.query.filter_by(name=branch_name).first()
    profile = StudentProfile(
        user_id=user.id, contact_number='9800000000', approval_status=status,
        cgpa=cgpa, graduation_year=grad_year, branch_id=branch.id, skills=skills,
        experience='Built a few academic and personal projects.',
    )
    if status == StudentStatus.BLACKLISTED:
        user.is_active = False
    db.session.add(profile)
    db.session.flush()
    return profile


def make_drive(company, job_title, status, cgpa, target_year, branch_names, days_from_now, skills, salary):
    existing = PlacementDrive.query.filter_by(company_id=company.id, job_title=job_title).first()
    if existing:
        return existing
    branches = Branch.query.filter(Branch.name.in_(branch_names)).all()
    drive = PlacementDrive(
        company_id=company.id, job_title=job_title, job_description=f'{job_title} role at {company.company_name}.',
        location='Bengaluru', job_type='Full-time', contact_phone='9876500000',
        application_deadline=datetime.now(timezone.utc) + timedelta(days=days_from_now),
        cgpa=cgpa, target_year=target_year, skills_required=skills, salary=salary,
        status=status, allowed_branches=branches,
    )
    db.session.add(drive)
    db.session.flush()
    return drive


def make_application(student, drive, status, offered_salary=None, joining_date=None):
    existing = Application.query.filter_by(student_id=student.id, drive_id=drive.id).first()
    if existing:
        return existing
    application = Application(
        student_id=student.id, drive_id=drive.id, status=status,
        offered_salary=offered_salary, offered_joining_date=joining_date,
    )
    db.session.add(application)
    db.session.flush()
    return application


def run():
    with app.app_context():
        db.create_all()
        seed_branches()
        seed_admin()
        db.session.commit()

        acme = make_company('HR Priya', 'company1@placement.com', 'Acme Corp', 'Software', 'https://acme.example.com', CompanyStatus.APPROVED)
        beta = make_company('HR Rohan', 'company2@placement.com', 'Beta Inc', 'Finance', 'https://beta.example.com', CompanyStatus.APPROVED)
        make_company('HR Neha', 'company3@placement.com', 'Gamma Tech', 'Analytics', 'https://gamma.example.com', CompanyStatus.PENDING)
        make_company('HR Karan', 'company4@placement.com', 'Delta Systems', 'Hardware', 'https://delta.example.com', CompanyStatus.REJECTED)
        make_company('HR Simran', 'company5@placement.com', 'Epsilon Labs', 'Biotech', 'https://epsilon.example.com', CompanyStatus.BLACKLISTED)
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
        d_devops = make_drive(acme, 'DevOps Engineer', PlacementDriveStatus.CLOSED, 7.5, 2027, ['Computer Science', 'Information Technology'], 10, 'Docker, AWS', 1100000)
        d_intern = make_drive(acme, 'Software Intern', PlacementDriveStatus.CANCELLED, 6.0, 2026, ['Computer Science'], 15, 'Python', 400000)
        d_backend = make_drive(acme, 'Backend Developer', PlacementDriveStatus.REJECTED, 7.0, 2027, ['Computer Science'], 20, 'Node.js', 1000000)
        d_pm = make_drive(beta, 'Product Manager', PlacementDriveStatus.APPROVED, 8.0, 2027, ['Computer Science', 'Information Technology', 'Electronics & Communication'], 40, 'Product Strategy', 1500000)
        d_qa = make_drive(beta, 'QA Engineer', PlacementDriveStatus.APPROVED, 6.0, 2028, ['Computer Science', 'Electrical Engineering'], 35, 'Selenium, Testing', 800000)
        db.session.commit()

        aarav, diya, kabir, isha, vivaan, ananya, reyansh, myra, arjun, sara = students

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

        if not app_interview.interviews:
            db.session.add(InterviewSchedule(
                application_id=app_interview.id,
                scheduled_date_time=datetime.now(timezone.utc) + timedelta(days=3),
                interviewer_name='Priya Sharma', meeting_link='https://meet.example.com/swe-interview',
                status=InterviewStatus.SCHEDULED,
            ))

        if not app_placed.placement:
            db.session.add(Placement(
                student_id=ananya.id, company_id=beta.id, drive_id=d_pm.id, application_id=app_placed.id,
                position=d_pm.job_title, salary_offered=app_placed.offered_salary, joining_date=app_placed.offered_joining_date,
            ))
        db.session.commit()
        print('Seed data created successfully.')


if __name__ == '__main__':
    run()
