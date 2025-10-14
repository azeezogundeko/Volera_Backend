import asyncio
import time

from db import user_db
from utils.email_manager  import manager
from appwrite.query import Query

def get_html_content(name: str):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Start Shopping on Volera Today!</title>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; background-color: #f9fafb; }}
            .container {{ 
                width: 100%; 
                max-width: 600px; 
                margin: auto; 
                padding: 20px; 
            }}
            .main-card {{ 
                background: white; 
                padding: 30px; 
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .feature-highlights {{
                display: flex;
                justify-content: space-around;
                flex-wrap: wrap;
                margin: 30px 0;
                text-align: center;
            }}
            .highlight {{
                flex: 1;
                min-width: 120px;
                margin: 10px;
                padding: 15px;
                background: #f8fafc;
                border-radius: 8px;
            }}
            .benefits {{
                margin: 30px 0;
                padding: 20px;
                background: #f8fafc;
                border-radius: 8px;
            }}
            .benefit {{ 
                font-size: 17px; 
                margin-bottom: 15px;
                padding-left: 10px;
                border-left: 4px solid #10B981;
            }}
            .cta {{ 
                text-align: center;
                margin: 30px 0;
            }}
            .btn {{ 
                display: inline-block; 
                padding: 12px 25px; 
                color: white; 
                background-color: #10B981; 
                text-decoration: none; 
                border-radius: 6px;
                font-weight: bold;
            }}
            .social-links {{
                margin: 30px 0 20px;
                text-align: center;
            }}
            .footer {{ 
                text-align: center;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #e5e7eb;
                color: #6b7280;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="main-card">
                <div class="header">
                    <h1 style="color: #10B981; margin-bottom: 10px;">Hey {name}, ready to shop? 🛍️</h1>
                    <p style="font-size: 18px; color: #374151;">Discover and shop your favorite products all in one place.</p>
                </div>

                <h2 style="color: #10B981; margin: 25px 0;">Why Shop on Volera?</h2>
                <p style="font-size: 17px; line-height: 1.6;">At Volera, we bring you the best deals, the widest selection, and an AI-driven experience that makes shopping a breeze. Say goodbye to endless browsing and hello to smart, seamless shopping!</p>
                
                <div class="feature-highlights">
                    <div class="highlight">
                        <h3>🔍 Curated Picks</h3>
                        <p>Hand-picked by AI</p>
                    </div>
                    <div class="highlight">
                        <h3>⚡ Fast Checkout</h3>
                        <p>Secure & seamless</p>
                    </div>
                    <div class="highlight">
                        <h3>💰 Best Prices</h3>
                        <p>Compare & save</p>
                    </div>
                </div>

                <div class="benefits">
                    <div class="benefit">🛒 One-stop shop across top retailers</div>
                    <div class="benefit">💡 Personalized recommendations just for you</div>
                    <div class="benefit">📦 Real-time stock & price updates</div>
                    <div class="benefit">🔒 Protected payments & buyer support</div>
                </div>

                <div class="cta">
                    <h3 style="color: #10B981;">Ready to Start Shopping?</h3>
                    <p style="font-size: 17px; line-height: 1.6;">Click below to explore deals and products curated by Volera's AI.</p>
                    <a href="https://www.volera.app/shop" class="btn">Shop Now on Volera</a>
                </div>
                
                <div class="social-links">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0">
                        <tr>
                            <td align="center">
                                <table border="0" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td align="center" style="padding: 0 10px;">
                                            <a href="https://x.com/volera4727" title="Follow us on X">
                                                <img src="https://about.twitter.com/content/dam/about-twitter/x/brand-toolkit/logo-black.png.twimg.1920.png" alt="X" width="32" height="32" style="display: block;">
                                            </a>
                                        </td>
                                        <td align="center" style="padding: 0 10px;">
                                            <a href="https://www.youtube.com/@volera1-v4i" title="Subscribe on YouTube">
                                                <img src="https://www.youtube.com/s/desktop/7c155e84/img/favicon_144x144.png" alt="YouTube" width="32" height="32" style="display: block;">
                                            </a>
                                        </td>
                                        <td align="center" style="padding: 0 10px;">
                                            <a href="https://www.linkedin.com/company/volera" title="Connect on LinkedIn">
                                                <img src="https://static.licdn.com/aero-v1/sc/h/al2o9zrvru7aqj8e1x2rzsrca" alt="LinkedIn" width="32" height="32" style="display: block;">
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </div>

                <div class="footer">
                    <p>© 2025 Volera. All rights reserved.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    '''



def get_all_users():
    all_users = user_db.list([Query.limit(100)])

    users = all_users['users']
    print(len(users))
    result = [{
        'email': user['email'],
        'name': user['name'].split('_')[0]
    } for user in users]
    return result[3:]
    # return [
    #     {
    #         'email': 'azeezogundeko19@gmail.com',
    #         'name': 'azeez'
    #     }
    # ]


def send_email():
    users = get_all_users()
    manager.choose_account('azeez_volera')
    
    users = [user for user in users if user['email']]
    
    max_retries = 3
    sleep_time = 5

    for user in users:
        retries = 0
        while retries < max_retries:
            try:
                manager.send_email(
                    user['email'],
                    subject='Unlock Exclusive Savings on Volera Today!',
                    html_content=get_html_content(user['name'])
                )
                print(f'Successfully sent email to {user["email"]} (attempt {retries + 1})')
                print(f'sleeping for {sleep_time} seconds')
                time.sleep(sleep_time)
                break
            except Exception as e:
                retries += 1
                if retries < max_retries:
                    print(f'Failed to send email to {user["email"]}, attempt {retries} of {max_retries}: {str(e)}')
                    time.sleep(sleep_time * 2)
                else:
                    print(f'All retries failed for {user["email"]}: {str(e)}')

if __name__ == '__main__':
    send_email()