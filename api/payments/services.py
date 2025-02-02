from utils.email_templates.payment_acknowledgement import get_payment_acknowlegement
from utils.emails import send_email
from fastapi import BackgroundTasks


def send_payment_acknowledgement(reference, amount, credits, email, b: BackgroundTasks):
    html_content = get_payment_acknowlegement(reference, amount, credits)
    b.add_task(send_email, email, html_content, "Payment Acknowledgement - Volera")