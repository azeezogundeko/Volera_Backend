def get_forgot_password_html(user_name, verification_code):
    return f""" 
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Password Reset Verification - Volera</title>
            <style>
                /* General Styles */
                body {{
                margin: 0;
                padding: 0;
                background-color: #f2f2f2;
                font-family: Arial, sans-serif;
                }}
                table {{
                border-spacing: 0;
                }}
                td {{
                padding: 0;
                }}
                .container {{
                width: 100%;
                background-color: #f2f2f2;
                padding: 20px 0;
                }}
                .email-content {{
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border: 1px solid #dddddd;
                }}
                .header {{
                background-color: #4CAF50;
                color: #ffffff;
                padding: 20px;
                text-align: center;
                font-size: 24px;
                }}
                .body {{
                padding: 30px 20px;
                color: #333333;
                font-size: 16px;
                line-height: 1.5;
                }}
                .verification-code {{
                display: inline-block;
                background-color: #f9f9f9;
                padding: 10px 20px;
                font-size: 20px;
                letter-spacing: 2px;
                border: 1px dashed #cccccc;
                margin: 20px 0;
                }}
                .footer {{
                text-align: center;
                padding: 20px;
                font-size: 14px;
                color: #777777;
                background-color: #fafafa;
                border-top: 1px solid #dddddd;
                }}
                a {{
                color: #4CAF50;
                text-decoration: none;
                }}
                @media only screen and (max-width: 600px) {{
                .email-content {{
                    width: 100% !important;
                }}
                }}
            </style>
            </head>
            <body>
            <table class="container" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                <td align="center">
                    <table class="email-content" cellpadding="0" cellspacing="0">
                    <!-- Header -->
                    <tr>
                        <td class="header">
                        Password Reset Request
                        </td>
                    </tr>
                    <!-- Body -->
                    <tr>
                        <td class="body">
                        <p>Hi {user_name},</p>
                        <p>We received a request to reset your password. To proceed with resetting your password, please use the verification code below:</p>
                        <div style="text-align: center;">
                            <span class="verification-code">{verification_code}</span>
                        </div>
                        <p>If you did not request a password reset, please ignore this email or contact our support team.</p>
                        <p>Thank you,<br>The Support Team</p>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td class="footer">
                        <p>If you’re having trouble, please <a href="mailto:support@example.com">contact support</a>.</p>
                        <p>&copy; 2025 Your Company. All rights reserved.</p>
                        </td>
                    </tr>
                    </table>
                </td>
                </tr>
            </table>
            </body>
            </html>

    
    """