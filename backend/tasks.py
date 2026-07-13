import csv
import io
from datetime import datetime, timedelta, timezone

from flask_mail import Message

from celery_workers import celery
from models import (
    db, mail, User, Role,
    StudentProfile, CompanyProfile, CompanyStatus, StudentStatus,
    PlacementDrive, PlacementDriveStatus,
    Application, ApplicationStatus,
    Placement, NotificationLog,
)

ACTIVE_STATUSES = [ApplicationStatus.APPLIED, ApplicationStatus.SHORTLISTED, ApplicationStatus.INTERVIEW]


def log_notification(job_type, recipient_email, status, error_message=None):
    db.session.add(NotificationLog(job_type=job_type, recipient_email=recipient_email, status=status, error_message=error_message))
    db.session.commit()


@celery.task(name='tasks.send_daily_reminders')
def send_daily_reminders():
    now = datetime.utcnow()
    window_end = now + timedelta(hours=48)
    drives = PlacementDrive.query.filter(
        PlacementDrive.status == PlacementDriveStatus.APPROVED,
        PlacementDrive.application_deadline >= now,
        PlacementDrive.application_deadline <= window_end,
    ).all()

    sent = 0
    students = StudentProfile.query.join(User).filter(
        User.is_active == True,
        StudentProfile.approval_status == StudentStatus.APPROVED
    ).all()

    for drive in drives:
        applied_student_ids = {app.student_id for app in drive.applications}
        for student in students:
            if student.id in applied_student_ids:
                continue

            # Branch eligibility check
            if drive.allowed_branches and student.branch_id not in [b.id for b in drive.allowed_branches]:
                continue

            # Target graduation year check
            if not (drive.min_target_year <= student.graduation_year <= drive.max_target_year):
                continue

            # CGPA eligibility check
            if drive.cgpa and student.cgpa < drive.cgpa:
                continue

            student_email = student.user.email
            try:
                mail.send(Message(
                    subject=f'Reminder: Apply to {drive.job_title} at {drive.company.company_name}',
                    recipients=[student_email],
                    body=(
                        f'Hi {student.user.name},\n\n'
                        f'Apply now for the placement drive "{drive.job_title}" at {drive.company.company_name}. '
                        f'The application deadline is on {drive.application_deadline.strftime("%d %b %Y, %H:%M")}.\n'
                        f'Don\'t miss this opportunity!\n\nPlacementPro'
                    ),
                ))
                log_notification('DAILY_REMINDER', student_email, 'sent')
                sent += 1
            except Exception as exc:
                log_notification('DAILY_REMINDER', student_email, 'failed', str(exc))
    return {'reminders_sent': sent}


@celery.task(name='tasks.generate_monthly_report')
def generate_monthly_report():
    now = datetime.utcnow()
    period_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1)
    period_end = now.replace(day=1)

    drives_conducted = PlacementDrive.query.filter(
        PlacementDrive.created_at >= period_start, PlacementDrive.created_at < period_end
    ).count()
    applications_count = Application.query.filter(
        Application.created_at >= period_start, Application.created_at < period_end
    ).count()
    placements_count = Placement.query.filter(
        Placement.created_at >= period_start, Placement.created_at < period_end
    ).count()

    admin = User.query.filter_by(role=Role.ADMIN).first()
    if not admin:
        return {'sent': False, 'reason': 'no admin found'}

    html = f'''
    <h2>PlacementPro Monthly Activity Report</h2>
    <p>Period: {period_start.strftime("%B %Y")}</p>
    <ul>
      <li>Placement drives conducted: {drives_conducted}</li>
      <li>Applications submitted: {applications_count}</li>
      <li>Students placed: {placements_count}</li>
    </ul>
    '''
    try:
        mail.send(Message(subject='PlacementPro Monthly Activity Report', recipients=[admin.email], html=html))
        log_notification('MONTHLY_REPORT', admin.email, 'sent')
        return {'sent': True}
    except Exception as exc:
        log_notification('MONTHLY_REPORT', admin.email, 'failed', str(exc))
        return {'sent': False, 'reason': str(exc)}


@celery.task(name='tasks.export_applications_csv')
def export_applications_csv(student_id):
    student = StudentProfile.query.get(student_id)
    if not student:
        return {'csv': '', 'filename': 'applications.csv'}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(['Student ID', 'Company Name', 'Drive Title', 'Status', 'Application Date'])
    for application in student.applications:
        writer.writerow([
            student.id,
            application.drive.company.company_name,
            application.drive.job_title,
            application.status.name,
            application.application_date.isoformat() if application.application_date else '',
        ])
    safe_name = student.user.name.strip().replace(' ', '_')
    return {'csv': buffer.getvalue(), 'filename': f'{safe_name}_placement_history.csv'}
