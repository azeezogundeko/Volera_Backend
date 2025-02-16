def get_new_user_html(verification_code: str) -> str:
    """
    Generate HTML content for the new user verification email.
    
    Args:
        verification_code: The verification code to be included in the email
        
    Returns:
        str: HTML content for the email
    """
    return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #1a1a1a; font-size: 28px; margin-bottom: 10px;">Verify Your Email</h1>
                <div style="display: inline-block; padding: 8px 16px; background: rgba(16, 185, 129, 0.1); border-radius: 20px; margin-bottom: 20px;">
                    <span style="color: #10b981; font-size: 14px;">Welcome to Volera</span>
                </div>
            </div>

            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 24px; margin-bottom: 30px;">
                <p style="color: #4b5563; line-height: 1.6; margin-bottom: 20px;">
                    Thank you for signing up! To complete your registration and start using Volera, please use the verification code below:
                </p>

                <div style="text-align: center; margin: 30px 0;">
                    <div style="background: #ffffff; border: 2px solid #10b981; border-radius: 8px; padding: 16px; display: inline-block;">
                        <span style="font-size: 24px; font-weight: bold; letter-spacing: 4px; color: #1a1a1a;">{verification_code}</span>
                    </div>
                </div>

                <p style="color: #4b5563; line-height: 1.6; margin-top: 20px;">
                    This code will expire in 10 minutes. If you didn't request this verification, please ignore this email.
                </p>
            </div>

            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                <p style="color: #6b7280; font-size: 14px; margin-bottom: 10px;">Need help? Contact our support team</p>
                <div style="margin-top: 15px;">
                    <a href="https://volera.app" style="color: #10b981; text-decoration: none; margin: 0 10px;">Website</a>
                    <a href="https://volera.app/contact" style="color: #10b981; text-decoration: none; margin: 0 10px;">Support</a>
                </div>
            </div>
        </div>
    """ 