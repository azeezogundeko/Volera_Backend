from utils.email_manager import manager
from utils.email_templates.forgot_password import get_forgot_password_html


def send_forgot_password_email(email, user_name, verification_code):
    manager.choose_account("no-reply")
    content = get_forgot_password_html(user_name, verification_code)
    manager.send_email(to_email=email, html_content=content, subject="Password Reset Verification - Volera")