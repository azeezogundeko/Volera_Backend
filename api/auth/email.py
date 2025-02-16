from utils.email_manager import manager
from utils.email_templates.forgot_password import get_forgot_password_html
from utils.celery_tasks import send_email


def send_forgot_password_email(email, user_name, verification_code):
    content = get_forgot_password_html(user_name, verification_code)
    
    # Send password reset email with high priority using Celery
    send_email.apply_async(
        args=[
            email,  # to_email
            "Password Reset Verification - Volera",  # subject
            content,  # html_content
        ],
        kwargs={
            'account_key': "no-reply",
            'priority': 'high'
        },
        queue='high_priority'
    )