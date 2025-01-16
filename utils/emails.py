import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from email.mime.application import MIMEApplication
from dotenv import load_dotenv
from .logging import logger

load_dotenv()

from_email = os.getenv("FROM_EMAIL")
smtp_password = os.getenv("SMTP_PASSWORD")
from_email = os.environ.get("FROM_EMAIL")
smtp_password = os.environ.get("SMTP_PASSWORD")
smtp_server = "smtp.gmail.com"
smtp_port = 465


def send_email(
    to_email,
    content,
    subject=None,
    attachments=None,
    recipients=None,
):
    # Create a MIMEMultipart message
    message = MIMEMultipart("alternative")
    message["To"] = to_email
    message["Subject"] = subject
    message["From"] = from_email
    if recipients:
        message["Bcc"] = ", ".join(recipients)

    # Add additional headers that can improve deliverability
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=from_email.split("@")[1])
    message["MIME-Version"] = "1.0"
    message["X-Priority"] = "3"  # Normal priority
    message["X-Mailer"] = "Python Email Client"

    # Optional but recommended headers
    message["Reply-To"] = from_email
    message["Return-Path"] = from_email

    # Attach plain text and HTML versions of the message
    # message.attach(MIMEText(text_content, "plain"))
    message.attach(MIMEText(content, "html"))

    # Attach files if any
    if attachments:
        for attachment in attachments:
            filename = attachment.filename
            try:
                attachment_data = attachment.file.read()
            except Exception as e:
                print(f"Error reading attachment: {e}")
                continue  # Skip this attachment on error
            else:
                attachment_mime = MIMEApplication(attachment_data)
                attachment_mime.add_header(
                    "Content-Disposition", f"attachment; filename={filename}"
                )
                message.attach(attachment_mime)

    # Modified SMTP connection and sending with more detailed error handling
    try:
        smtp = smtplib.SMTP_SSL(smtp_server, smtp_port)
        smtp.login(from_email, smtp_password)
        smtp.send_message(message)
        logger.info(f"Email sent to {to_email}")

    except Exception as e:
        print(f"Failed to send email: {e}")
        raise
    finally:
        smtp.quit()


def send_new_user_email(verification_code, email):
    from datetime import datetime

    year = datetime.now().year
    subject = "Verify Your Email - Volera"
    html_content = new_users_template(verification_code, year)
    send_email(email, html_content, subject)

def new_users_template(verification_code, year):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - ShopLM</title>
    <style>
        body {{
        font-family: 'Arial', sans-serif;
        background-color: #f4f4f7;
        color: #51545e;
        margin: 0;
        padding: 0;
        }}
        .email-wrapper {{
        width: 100%;
        background-color: #f4f4f7;
        padding: 20px 0;
        }}
        .email-content {{
        max-width: 600px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .email-header {{
        background-color: #007bff;
        color: #ffffff;
        text-align: center;
        padding: 20px;
        }}
        .email-header h1 {{
        margin: 0;
        font-size: 24px;
        }}
        .email-body {{
        padding: 20px;
        text-align: center;
        }}
        .email-body h2 {{
        color: #333333;
        font-size: 20px;
        margin-bottom: 10px;
        }}
        .email-body p {{
        font-size: 16px;
        margin: 0 0 20px;
        line-height: 1.6;
        color: #51545e;
        }}
        .verification-code {{
        font-size: 24px;
        font-weight: bold;
        color: #007bff;
        background-color: #f0f8ff;
        padding: 10px 20px;
        border-radius: 4px;
        display: inline-block;
        letter-spacing: 2px;
        margin: 20px 0;
        }}
        .email-footer {{
        text-align: center;
        font-size: 12px;
        color: #999999;
        padding: 20px;
        background-color: #f4f4f7;
        }}
        .email-footer a {{
        color: #007bff;
        text-decoration: none;
        }}
        @media only screen and (max-width: 600px) {{
        .email-content {{
            margin: 0 10px;
        }}
        }}
    </style>
    </head>
    <body>
    <div class="email-wrapper">
        <div class="email-content">
        <!-- Header -->
        <div class="email-header">
            <h1>ShopLM</h1>
        </div>
        <!-- Body -->
        <div class="email-body">
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up for Volera! To complete your registration, please use the verification code below:</p>
            <div class="verification-code">{verification_code}</div>
            <p>Enter this code in the ShopLM app to verify your email address.</p>
            <p>If you didn’t request this, you can safely ignore this email.</p>
        </div>
        <!-- Footer -->
        <div class="email-footer">
            <p> {year} Volera. All rights reserved.</p>
            <p>
            <a href="https://shoplm.com/terms">Terms of Service</a> | 
            <a href="https://shoplm.com/privacy">Privacy Policy</a>
            </p>
        </div>
        </div>
    </div>
    </body>
    </html>
    """