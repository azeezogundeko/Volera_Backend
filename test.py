import asyncio
import time

from db import user_db
from utils.email_manager  import manager


from appwrite.query import Query



def get_html_content(name: str):
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background-color: #059669;
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .content {{
                padding: 30px;
                background-color: #ffffff;
                border: 1px solid #e5e7eb;
            }}
            .features {{
                background-color: #f3f4f6;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
            }}
            .feature-item {{
                margin: 10px 0;
                color: #374151;
            }}
            .button {{
                display: inline-block;
                background-color: #059669;
                color: white;
                padding: 12px 25px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                background: linear-gradient(to right, #059669, #047857);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 0 0 8px 8px;
            }}
            .footer-content {{
                max-width: 500px;
                margin: 0 auto;
            }}
            .social-links {{
                margin: 25px auto;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
                max-width: 400px;
            }}
            .social-links a {{
                color: white;
                text-decoration: none;
                background-color: rgba(255, 255, 255, 0.1);
                padding: 12px 20px;
                border-radius: 5px;
                transition: all 0.3s ease;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                min-width: 120px;
                text-align: center;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            .social-links a:hover {{
                background-color: rgba(255, 255, 255, 0.2);
                transform: translateY(-2px);
                border-color: rgba(255, 255, 255, 0.4);
            }}
            .social-icon {{
                width: 20px;
                height: 20px;
                display: inline-block;
                vertical-align: middle;
            }}
            .footer-divider {{
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                margin: 20px 0;
            }}
            .footer-text {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to Volera!</h1>
            </div>
            
            <div class="content">
                <p>Dear {name},</p>
                
                <p>We're thrilled to welcome you to Volera, your ultimate shopping companion</p>
                
                <p>At Volera, we're revolutionizing how you shop online by bringing you the best deals across multiple platforms.</p>
                
                <div class="features">
                    <h2>What You Can Do with Volera:</h2>
                    <div class="feature-item">✓ Track prices across platforms in real-time</div>
                    <div class="feature-item">✓ Get personalized product recommendations</div>
                    <div class="feature-item">✓ Search products across Jumia, Jiji, and Konga in one place</div>
                    <div class="feature-item">✓ Save money with price alerts and comparisons</div>
                </div>
                
                <p>Ready to start your smart shopping journey?</p>
                
                <center>
                    <a href="https://www.volera.app/login" class="button">Login to Your Account</a>
                </center>
                
                <div class="signature">
                    <p>Best regards,</p>
                    <p><strong>Ogundeko Abdulazeez</strong><br>
                    CEO/Founder of Volera</p>
                </div>
            </div>
            
            <div class="footer">
                <div class="footer-content">
                    <h3 style="margin: 0; font-size: 20px; color: white;">Connect with Volera</h3>
                    <p class="footer-text" style="color: rgba(255, 255, 255, 0.9);">Join our community and stay updated with the latest features and deals</p>
                    
                    <div class="social-links">
                        <a href="https://x.com/volera4727" style="flex: 1;">
                            <svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                            </svg>
                            X (Twitter)
                        </a>
                        <a href="https://www.youtube.com/@volera1-v4i" style="flex: 1;">
                            <svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                            </svg>
                            YouTube
                        </a>
                        <a href="https://www.linkedin.com/company/volera" style="flex: 1;">
                            <svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                            </svg>
                            LinkedIn
                        </a>
                    </div>
                    
                    <div class="footer-divider"></div>
                    
                    <p class="footer-text" style="margin-bottom: 0;">© 2025 Volera. All rights reserved.</p>
                    <p class="footer-text" style="font-size: 12px; margin-top: 5px;">
                        Shop with Artificial Intelligience
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def get_all_users():
    all_users = user_db.list([Query.limit(100)])

    users = all_users['users']
    print(len(users))
    result = [{
        'email': user['email'],
        'name': user['name'].split('_')[0]
    } for user in users]
    return result
    # return [
    #     {
    #         'email': 'azeezogundeko@volera.app',
    #         'name': 'azeez'
    #     }
    # ]


def send_email():
    users = get_all_users()
    manager.choose_account('azeez_volera')
    for user in users:
        try:
            manager.send_email(
                user['email'],
                subject='Welcome to Volera',
                html_content=get_html_content(user['name'])
            )

            print(f'sent email to {user["email"]}')
            print('sleeping for 5 seconds')
            time.sleep(5)
        except Exception as e:
            print('could not send email to:', user['email'], str(e))
            continue

if __name__ == '__main__':
    send_email()

