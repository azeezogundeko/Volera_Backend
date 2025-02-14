from .email_manager import manager


def send_new_user_email(verification_code, email):
    from datetime import datetime
    manager.choose_account("no-reply")
    year = datetime.now().year
    subject = "Verify Your Email - Volera"
    html_content = new_users_template(verification_code, year)
    manager.send_email(email, subject, html_content)

def new_users_template(verification_code, year):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email - Volera</title>
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
            <h1>Volera</h1>
        </div>
        <!-- Body -->
        <div class="email-body">
            <h2>Verify Your Email Address</h2>
            <p>Thank you for signing up for Volera! To complete your registration, please use the verification code below:</p>
            <div class="verification-code">{verification_code}</div>
            <p>Enter this code in the Volera app to verify your email address.</p>
            <p>If you didn’t request this, you can safely ignore this email.</p>
        </div>
        <!-- Footer -->
        <div class="email-footer">
            <p> {year} Volera. All rights reserved.</p>
            <p>
            <a href="https://volera.app/terms">Terms of Service</a> | 
            <a href="https://volera.app/privacy">Privacy Policy</a>
            </p>
        </div>
        </div>
    </div>
    </body>
    </html>
    """

def waitlist_template(user_email, privacy_link):
    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>You're On the Volera Waitlist!</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="margin: 0; padding: 0; background-color: #ffffff; color: #1f2937; font-family: Arial, sans-serif;">
            
            <!-- Main Container -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; margin: 0 auto;">
                <tr>
                    <td style="padding: 40px 20px;">
                        
                        <!-- Header -->
                        <div style="text-align: center; margin-bottom: 40px;">
                            <h1 style="color: #34d399; margin: 0 0 10px 0; font-size: 28px;">Volera</h1>
                            <p style="color: #6b7280; margin: 0;">Your Smart Shopping Companion</p>
                        </div>

                        <!-- Confirmation Message -->
                        <div style="background: #f9fafb; border-radius: 12px; padding: 30px; margin-bottom: 40px;">
                            <p style="color: #34d399; text-align: center; margin: 0 0 15px 0;">
                                🎉 Welcome to the Future of Shopping!
                            </p>
                            <h2 style="font-size: 22px; text-align: center; margin: 0 0 20px 0;">
                                Hello {user_email},<br>You're Now on the Waitlist!
                            </h2>
                            <p style="color: #6b7280; line-height: 1.6; text-align: center;">
                                Thank you for joining our community of smart shoppers. While we prepare your access, here's what to expect:
                            </p>
                        </div>

                        <!-- Feature Highlights -->
                        <div style="background: #f9fafb; border-radius: 12px; padding: 30px; margin-bottom: 40px;">
                            <div style="margin-bottom: 25px;">
                                <h3 style="color: #34d399; margin: 0 0 15px 0;">🔮 Coming Soon:</h3>
                                <div style="color: #4b5563; padding-left: 20px;">
                                    <p style="margin: 15px 0;">✅ AI-powered product discovery across all major retailers</p>
                                    <p style="margin: 15px 0;">✅ Real-time price tracking & deal alerts</p>
                                    <p style="margin: 15px 0;">✅ Personalized shopping assistant 24/7</p>
                                </div>
                            </div>

                            <div style="border-top: 1px solid #e5e7eb; padding-top: 25px;">
                                <p style="color: #6b7280; text-align: center; line-height: 1.6;">
                                    "Volera helped me save 32% on my electronics purchases last year"<br>
                                    - Sarah J., Early Beta Tester
                                </p>
                            </div>
                        </div>

                        <!-- CEO Signature -->
                        <div style="text-align: center; margin-bottom: 30px; border-top: 1px solid #e5e7eb; padding-top: 30px;">
                            <p style="margin: 0 0 5px 0; color: #34d399; font-weight: bold;">Abdulazeez Ogundeko</p>
                            <p style="margin: 0; color: #6b7280;">CEO/Founder, Volera</p>
                        </div>

                        <!-- Footer -->
                        <div style="text-align: center; color: #6b7280; font-size: 12px;">
                            <p>Follow our journey:<br>
                            <a href="[LinkedIn Placeholder]" style="color: #6b7280; text-decoration: underline;">LinkedIn</a> |
                            <a href="[X Placeholder]" style="color: #6b7280; text-decoration: underline;">X</a> |
                            <a href="[Bluesky Placeholder]" style="color: #6b7280; text-decoration: underline;">Bluesky</a> |
                            <a href="[WhatsApp Community Placeholder]" style="color: #6b7280; text-decoration: underline;">Join our WhatsApp Community</a>
                            </p>
                            <p>© 2024 Volera. All rights reserved.</p>
                            <p>
                                <a href="{privacy_link}" style="color: #6b7280; text-decoration: underline;">Privacy Policy</a>
                            </p>
                        </div>

                    </td>
                </tr>
            </table>
        </body>
        </html>
    """

