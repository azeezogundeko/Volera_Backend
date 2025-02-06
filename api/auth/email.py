from utils.emails import send_email
from utils.email_templates.forgot_password import get_forgot_password_html


def send_forgot_password_email(email, user_name, verification_code):
    content = get_forgot_password_html(user_name, verification_code)
    send_email(to_email=email, content=content, subject="Password Reset Verification - Volera")