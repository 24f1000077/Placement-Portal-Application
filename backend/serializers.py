def student_to_dict(student):
    user = student.user
    return {
        'id': student.id,
        'user_id': user.id,
        'name': user.name,
        'email': user.email,
        'is_active': user.is_active,
        'contact_number': student.contact_number,
        'approval_status': student.approval_status.name,
        'cgpa': student.cgpa,
        'graduation_year': student.graduation_year,
        'branch_id': student.branch_id,
        'branch': student.branch_details.name if student.branch_details else None,
        'skills': student.skills,
        'experience': student.experience,
        'has_resume': student.resume is not None,
    }


def company_to_dict(company):
    user = company.user
    return {
        'id': company.id,
        'user_id': user.id,
        'name': user.name,
        'email': user.email,
        'is_active': user.is_active,
        'company_name': company.company_name,
        'hr_contact': company.hr_contact,
        'industry': company.industry,
        'website': company.website,
        'approval_status': company.approval_status.name,
    }


def drive_to_dict(drive, include_applicant_count=True):
    payload = {
        'id': drive.id,
        'company_id': drive.company_id,
        'company_name': drive.company.company_name,
        'job_title': drive.job_title,
        'job_description': drive.job_description,
        'location': drive.location,
        'job_type': drive.job_type,
        'contact_phone': drive.contact_phone,
        'application_deadline': drive.application_deadline.isoformat() if drive.application_deadline else None,
        'cgpa': drive.cgpa,
        'target_year': drive.target_year,
        'skills_required': drive.skills_required,
        'experience_required': drive.experience_required,
        'salary': drive.salary,
        'benefits': drive.benefits,
        'notes': drive.notes,
        'status': drive.status.name,
        'allowed_branches': [{'id': b.id, 'name': b.name} for b in drive.allowed_branches],
        'created_at': drive.created_at.isoformat() if drive.created_at else None,
    }
    if include_applicant_count:
        payload['applicant_count'] = len(drive.applications)
    return payload


def interview_to_dict(interview):
    return {
        'id': interview.id,
        'application_id': interview.application_id,
        'scheduled_date_time': interview.scheduled_date_time.isoformat() if interview.scheduled_date_time else None,
        'meeting_link': interview.meeting_link,
        'interviewer_name': interview.interviewer_name,
        'notes': interview.notes,
        'feedback': interview.feedback,
        'status': interview.status.name,
    }


def placement_to_dict(placement):
    return {
        'id': placement.id,
        'position': placement.position,
        'salary_offered': placement.salary_offered,
        'joining_date': placement.joining_date.isoformat() if placement.joining_date else None,
        'has_offer_letter': placement.offer_letter is not None,
    }


def application_to_dict(application, include_interviews=True):
    student = application.student
    drive = application.drive
    payload = {
        'id': application.id,
        'status': application.status.name,
        'application_date': application.application_date.isoformat() if application.application_date else None,
        'feedback': application.feedback,
        'student_id': student.id,
        'student_name': student.user.name,
        'student_email': student.user.email,
        'student_cgpa': student.cgpa,
        'student_branch': student.branch_details.name if student.branch_details else None,
        'has_resume': student.resume is not None,
        'drive_id': drive.id,
        'job_title': drive.job_title,
        'drive_status': drive.status.name,
        'company_id': drive.company_id,
        'company_name': drive.company.company_name,
    }
    if include_interviews:
        payload['interviews'] = [interview_to_dict(i) for i in application.interviews]
        payload['placement'] = placement_to_dict(application.placement) if application.placement else None
    return payload
