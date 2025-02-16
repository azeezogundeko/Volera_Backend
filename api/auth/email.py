from utils.email_manager import manager
from utils.email_templates.forgot_password import get_forgot_password_html
from utils.celery_tasks import send_email
from utils.email_templates.new_user import get_new_user_html


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

def send_new_user_email(verification_code: str, email: str):
    """
    Send welcome email to new users with verification code using Celery task.
    
    Args:
        verification_code: The verification code for email verification
        email: The user's email address
    """
    content = get_new_user_html(verification_code)
    
    # Send new user email with high priority using Celery
    send_email.apply_async(
        args=[
            email,  # to_email
            "Welcome to Volera - Email Verification",  # subject
            content,  # html_content
        ],
        kwargs={
            'account_key': "no-reply",
            'priority': 'high'
        },
        queue='high_priority'
    )

def send_formal_welcome_email(email: str, user_data: dict):
    """
    Send a formal welcome email after profile creation using Celery task.
    
    Args:
        email: The user's email address
        user_data: Dictionary containing user profile information
    """
    # Create a personalized welcome message with brand styling
    content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; color: #1a1a1a;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #1a1a1a; font-size: 28px; margin-bottom: 10px;">Welcome to Volera!</h1>
                <div style="display: inline-block; padding: 8px 16px; background: rgba(16, 185, 129, 0.1); border-radius: 20px; margin-bottom: 20px;">
                    <span style="color: #10b981; font-size: 14px;">AI-Powered Shopping Assistant</span>
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 30px;">
                <p style="color: #1a1a1a; font-size: 16px; margin-bottom: 20px;">Dear {user_data.get('first_name', '')},</p>
                
                <p style="color: #4b5563; line-height: 1.6; margin-bottom: 20px;">
                    Welcome to the future of e-commerce! We're thrilled to have you join our community of smart shoppers.
                </p>

                <div style="margin-bottom: 25px;">
                    <h3 style="color: #10b981; font-size: 18px; margin-bottom: 15px;">Experience the Power of AI Shopping:</h3>
                    <ul style="color: #4b5563; list-style: none; padding: 0; margin: 0;">
                        <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                            <span style="color: #10b981; position: absolute; left: 0;">✓</span>
                            Smart Product Search
                        </li>
                        <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                            <span style="color: #10b981; position: absolute; left: 0;">✓</span>
                            Real-time Price Analysis
                        </li>
                        <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                            <span style="color: #10b981; position: absolute; left: 0;">✓</span>
                            Personalized Recommendations
                        </li>
                        <li style="margin-bottom: 12px; padding-left: 24px; position: relative;">
                            <span style="color: #10b981; position: absolute; left: 0;">✓</span>
                            Market Intelligence
                        </li>
                    </ul>
                </div>

                <p style="color: #4b5563; text-align: right; font-style: italic; margin-top: 20px;">
                    - Team Volera
                </p>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 10px;">Need help? Contact our support team</p>
                <div style="margin-top: 15px; margin-bottom: 20px;">
                    <a href="https://volera.app" style="color: #10b981; text-decoration: none; margin: 0 10px;">Website</a>
                    <a href="https://volera.app/contact" style="color: #10b981; text-decoration: none; margin: 0 10px;">Support</a>
                    <a href="https://volera.app/faq" style="color: #10b981; text-decoration: none; margin: 0 10px;">FAQ</a>
                </div>
                <div style="margin-top: 15px;">
                    <a href="https://x.com/volera4727" style="display: inline-block; margin: 0 10px;">
                        <img src="https://about.twitter.com/content/dam/about-twitter/x/brand-toolkit/logo-black.png.twimg.1920.png" alt="X (Twitter)" style="width: 24px; height: 24px;">
                    </a>
                    <a href="https://www.linkedin.com/company/volera/" style="display: inline-block; margin: 0 10px;">
                        <img src="https://static.licdn.com/aero-v1/sc/h/al2o9zrvru7aqj8e1x2rzsrca" alt="LinkedIn" style="width: 24px; height: 24px;">
                    </a>
                </div>
            </div>
        </div>
    """

    # Send formal welcome email with high priority using Celery and support account
    send_email.apply_async(
        args=[
            email,  # to_email
            "Welcome to Volera - Your AI Shopping Assistant",  # subject
            content,  # html_content
        ],
        kwargs={
            'account_key': "support",  # Using support account
            'priority': 'high',
            'from_name': "Support Team"  # Adding a personal touch
        },
        queue='high_priority'
    )