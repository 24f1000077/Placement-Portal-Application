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
