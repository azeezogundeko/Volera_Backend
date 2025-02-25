"""Email templates for the admin system."""

# Base template with emerald green branding and enhanced styling
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {{
            --primary-color: #10B981;  /* Emerald 500 */
            --primary-dark: #059669;   /* Emerald 600 */
            --primary-light: #A7F3D0;  /* Emerald 200 */
            --primary-lighter: #D1FAE5; /* Emerald 100 */
            --text-dark: #1F2937;
            --text-light: #6B7280;
            --background: #F9FAFB;
            --white: #FFFFFF;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-dark);
            margin: 0;
            padding: 0;
            background-color: var(--background);
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            padding: 0;
            background-color: var(--white);
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            padding: 30px 20px;
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
            color: var(--white);
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px;
            background-color: var(--white);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-light);
            font-size: 12px;
            background-color: var(--primary-lighter);
            border-radius: 0 0 8px 8px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 28px;
            background: var(--primary-color);
            color: var(--white);
            text-decoration: none;
            border-radius: 6px;
            margin: 20px 0;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
        }}
        .button:hover {{
            background: var(--primary-dark);
            transform: translateY(-1px);
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);
        }}
        .list {{
            margin: 15px 0;
            padding-left: 20px;
        }}
        .list li {{
            margin-bottom: 10px;
        }}
        .highlight {{
            background-color: var(--primary-lighter);
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
            border-left: 4px solid var(--primary-color);
        }}
        .card {{
            border: 1px solid var(--primary-light);
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
            background-color: var(--white);
            transition: all 0.3s ease;
        }}
        .card:hover {{
            box-shadow: 0 4px 6px rgba(16, 185, 129, 0.1);
        }}
        .divider {{
            height: 1px;
            background-color: var(--primary-light);
            margin: 20px 0;
        }}
        a {{
            color: var(--primary-color);
            text-decoration: none;
        }}
        a:hover {{
            color: var(--primary-dark);
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

# Welcome Email Template
WELCOME_EMAIL = {
    "id": "1",
    "name": "Welcome Email",
    "subject": "Welcome to Volera! Let's Get Started",
    "description": "Sent to new users after registration",
    "last_used": "2024-03-15",
    "available_variables": ["name", "dashboard_url"],
    "content": """Hello {{name}},

    We're thrilled to welcome you to Volera! You've just joined a community of smart shoppers who never miss the best deals.

    Get Started in 3 Easy Steps:
    1. Set Up Your Profile - Customize your preferences for better recommendations
    2. Add Items to Your Wishlist - We'll track prices and notify you of drops
    3. Explore Smart Shopping - Use our AI-powered search to find the best deals

    Need Help?
    Our support team is here for you 24/7. Just reply to this email or visit our help center.

    Happy Shopping!
    The Volera Team""",
        "html_content": BASE_TEMPLATE.format(content="""
            <div class="header">
                <h1>Welcome to Volera! 🎉</h1>
            </div>
            <div class="content">
                <p>Hello {{name}},</p>
                
                <p>We're thrilled to welcome you to Volera! You've just joined a community of smart shoppers who never miss the best deals.</p>
                
                <div class="highlight">
                    <h3>Get Started in 3 Easy Steps:</h3>
                    <ol class="list">
                        <li><strong>Set Up Your Profile</strong> - Customize your preferences for better recommendations</li>
                        <li><strong>Add Items to Your Wishlist</strong> - We'll track prices and notify you of drops</li>
                        <li><strong>Explore Smart Shopping</strong> - Use our AI-powered search to find the best deals</li>
                    </ol>
                </div>
                
                <a href="{{dashboard_url}}" class="button">Go to Your Dashboard</a>
                
                <div class="card">
                    <h3>Need Help?</h3>
                    <p>Our support team is here for you 24/7. Just reply to this email or visit our help center.</p>
                </div>
                
                <p>Happy Shopping!<br>The Volera Team</p>
            </div>
            <div class="footer">
                <p>© 2024 Volera. All rights reserved.</p>
                <p>You received this email because you signed up for Volera.</p>
            </div>
        """)
}

# New Feature Announcement Template
NEW_FEATURE_ANNOUNCEMENT = {
    "id": "2",
    "name": "New Feature Announcement",
    "subject": "🚀 New Features Just Launched on Volera!",
    "description": "Announce new platform features to users",
    "last_used": "2024-03-14",
    "available_variables": ["name", "features", "login_url", "tutorial_url", "unsubscribe_url"],
    "content": """Hi {{name}},

    We've been working hard to make your Volera experience even better. Check out what's new:

    {{features}}

    Quick Tips:
    Watch our quick tutorial videos to make the most of these new features.
    Tutorial Link: {{tutorial_url}}

    Best regards,
    The Volera Team

    To unsubscribe from feature announcements, click here: {{unsubscribe_url}}""",
        "html_content": BASE_TEMPLATE.format(content="""
            <div class="header">
                <h1>New Features Are Here! 🚀</h1>
            </div>
            <div class="content">
                <p>Hi {{name}},</p>
                
                <p>We've been working hard to make your Volera experience even better. Check out what's new:</p>
                
                <div class="highlight">
                    {{features}}
                </div>
                
                <a href="{{login_url}}" class="button">Try New Features Now</a>
                
                <div class="card">
                    <h3>Quick Tips</h3>
                    <p>Watch our quick tutorial videos to make the most of these new features.</p>
                    <a href="{{tutorial_url}}">Watch Tutorials →</a>
                </div>
                
                <p>Best regards,<br>The Volera Team</p>
            </div>
            <div class="footer">
                <p>© 2024 Volera. All rights reserved.</p>
                <p><a href="{{unsubscribe_url}}">Unsubscribe from feature announcements</a></p>
            </div>
        """)
}

# Price Drop Alert Template
PRICE_DROP_ALERT = {
    "id": "3",
    "name": "Price Drop Alert",
    "subject": "💰 Price Drop Alert: Save on Your Wishlist Items!",
    "description": "Notify users about price drops",
    "available_variables": ["name", "items", "wishlist_url", "manage_alerts_url"],
    "last_used": "2024-03-15",
    "content": """Dear {{name}},

Great news! We've detected price drops on items you're watching:

{{items}}

Visit your wishlist to take advantage of these deals: {{wishlist_url}}

These are the lowest prices we've seen in the last 30 days!

Happy Saving!
The Volera Team

Manage your price alerts: {{manage_alerts_url}}""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>Price Drop Alert! 💰</h1>
        </div>
        <div class="content">
            <p>Dear {{name}},</p>
            
            <p>Great news! We've detected price drops on items you're watching:</p>
            
            <div class="highlight">
                {{items}}
            </div>
            
            <a href="{{wishlist_url}}" class="button">View Your Wishlist</a>
            
            <div class="card">
                <h3>Price History</h3>
                <p>These are the lowest prices we've seen in the last 30 days!</p>
            </div>
            
            <p>Happy Saving!<br>The Volera Team</p>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p><a href="{{manage_alerts_url}}">Manage your price alerts</a></p>
        </div>
    """)
}


# Monthly Summary Template
MONTHLY_SUMMARY = {
    "id": "4",
    "name": "Monthly Summary",
    "subject": "Your Volera Shopping Summary for {{month}}",
    "description": "Monthly user activity and savings summary",
    "last_used": "2024-03-01",
    "available_variables": ["month", "name", "total_savings", "items_purchased", "best_deal", "tracked_items", "alerts_count", "avg_discount", "recommendations", "dashboard_url", "email_preferences_url"],
    "content": """Hi {{name}},

Here's your Volera activity summary for {{month}}:

Your Savings:
- Total Saved: {{total_savings}}
- Items Purchased: {{items_purchased}}
- Best Deal: {{best_deal}}

Price Tracking Stats:
- Items Tracked: {{tracked_items}}
- Price Alerts Received: {{alerts_count}}
- Average Discount: {{avg_discount}}

View your full report: {{dashboard_url}}

Recommended for You:
{{recommendations}}

Update your email preferences: {{email_preferences_url}}""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>Your Monthly Summary 📊</h1>
        </div>
        <div class="content">
            <p>Hi {{name}},</p>
            
            <p>Here's your Volera activity summary for {{month}}:</p>
            
            <div class="highlight">
                <h3>Your Savings</h3>
                <p>Total Saved: {{total_savings}}</p>
                <p>Items Purchased: {{items_purchased}}</p>
                <p>Best Deal: {{best_deal}}</p>
            </div>
            
            <div class="card">
                <h3>Price Tracking Stats</h3>
                <ul class="list">
                    <li>Items Tracked: {{tracked_items}}</li>
                    <li>Price Alerts Received: {{alerts_count}}</li>
                    <li>Average Discount: {{avg_discount}}</li>
                </ul>
            </div>
            
            <a href="{{dashboard_url}}" class="button">View Full Report</a>
            
            <div class="card">
                <h3>Recommended for You</h3>
                {{recommendations}}
            </div>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p><a href="{{email_preferences_url}}">Update Email Preferences</a></p>
        </div>
    """)
}
# Support Reply Template
SUPPORT_REPLY = {
    "id": "5",
    "name": "Support Reply",
    "subject": "Re: {{ticket_subject}}",
    "description": "Personalized response to user inquiries",
    "last_used": "2024-03-15",
    "available_variables": ["name", "ticket_id", "ticket_subject", "response", "support_name", "follow_up_date", "support_portal_url", "faq_url", "help_center_url", "community_url"],
    "content": """Hi {{name}},

Thank you for reaching out about "{{ticket_subject}}".

Our Response:
{{response}}

Ticket Details:
- Ticket ID: #{{ticket_id}}
- Support Agent: {{support_name}}
- Follow-up Date: {{follow_up_date}}

Is there anything else you need help with?

View your ticket details: {{support_portal_url}}

Helpful Resources:
- FAQ: {{faq_url}}
- Help Center: {{help_center_url}}
- Community Forum: {{community_url}}

Best regards,
{{support_name}}
Volera Support Team""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>We're Here to Help 💬</h1>
        </div>
        <div class="content">
            <p>Hi {{name}},</p>
            
            <p>Thank you for reaching out about "{{ticket_subject}}".</p>
            
            <div class="highlight">
                <h3>Our Response</h3>
                <p>{{response}}</p>
            </div>
            
            <div class="card">
                <h3>Ticket Details</h3>
                <p><strong>Ticket ID:</strong> #{{ticket_id}}</p>
                <p><strong>Support Agent:</strong> {{support_name}}</p>
                <p><strong>Follow-up Date:</strong> {{follow_up_date}}</p>
            </div>
            
            <p>Is there anything else you need help with?</p>
            
            <a href="{{support_portal_url}}" class="button">View Ticket Details</a>
            
            <div class="card">
                <h3>Helpful Resources</h3>
                <ul class="list">
                    <li><a href="{{faq_url}}">Frequently Asked Questions</a></li>
                    <li><a href="{{help_center_url}}">Help Center</a></li>
                    <li><a href="{{community_url}}">Community Forum</a></li>
                </ul>
            </div>
            
            <p>Best regards,<br>{{support_name}}<br>Volera Support Team</p>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p>This is a direct response to your support ticket #{{ticket_id}}</p>
        </div>
    """)
}

# Newsletter Template
NEWSLETTER = {
    "id": "6",
    "name": "Newsletter",
    "subject": "🌟 {{newsletter_title}} - Volera's Monthly Digest",
    "description": "Monthly newsletter with shopping insights and trends",
    "last_used": "2024-03-15",
    "available_variables": ["name", "newsletter_title", "month_year", "featured_deals", "market_trends", "shopping_tips", "trending_items", "personalized_content", "newsletter_url", "email_preferences_url", "unsubscribe_url"],
    "content": """Dear {{name}},

{{newsletter_title}}
{{month_year}} Edition

Featured Deals of the Month:
{{featured_deals}}

Market Trends:
Stay ahead with the latest shopping trends and price insights:
{{market_trends}}

Smart Shopping Tips:
{{shopping_tips}}

Read the full newsletter: {{newsletter_url}}

Trending Now:
Most tracked items this month:
{{trending_items}}

Personalized For You:
Based on your interests:
{{personalized_content}}

Update your email preferences: {{email_preferences_url}}
Unsubscribe: {{unsubscribe_url}}""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>{{newsletter_title}} 📰</h1>
            <p style="margin: 10px 0 0; font-size: 16px;">{{month_year}} Edition</p>
        </div>
        <div class="content">
            <p>Dear {{name}},</p>
            
            <div class="highlight">
                <h3>🔥 Featured Deals of the Month</h3>
                {{featured_deals}}
            </div>
            
            <div class="card">
                <h3>📊 Market Trends</h3>
                <p>Stay ahead with the latest shopping trends and price insights:</p>
                {{market_trends}}
            </div>
            
            <div class="highlight">
                <h3>💡 Smart Shopping Tips</h3>
                {{shopping_tips}}
            </div>
            
            <a href="{{newsletter_url}}" class="button">Read Full Newsletter</a>
            
            <div class="card">
                <h3>🛍️ Trending Now</h3>
                <p>Most tracked items this month:</p>
                {{trending_items}}
            </div>
            
            <div class="card">
                <h3>🎯 Personalized For You</h3>
                <p>Based on your interests:</p>
                {{personalized_content}}
            </div>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p><a href="{{email_preferences_url}}">Update Email Preferences</a> | <a href="{{unsubscribe_url}}">Unsubscribe</a></p>
        </div>
    """)
}

# Re-engagement Template
REENGAGEMENT = {
    "id": "7",
    "name": "Re-engagement",
    "subject": "We Miss You at Volera! 🤗",
    "description": "Re-engage inactive users with personalized offers",
    "last_used": "2024-03-15",
    "available_variables": ["name", "days_inactive", "missed_deals", "special_offer", "login_url", "email_preferences_url", "unsubscribe_url"],
    "content": """Hi {{name}},

It's been {{days_inactive}} days since you last visited Volera, and we've noticed some amazing deals you might be interested in!

What You've Missed:
Price drops on items similar to your previous searches:
{{missed_deals}}

Special Welcome Back Offer:
{{special_offer}}

Return to Volera: {{login_url}}

Why Come Back?
- New AI-powered price tracking
- Improved deal alerts
- Enhanced shopping experience
- Exclusive member benefits

We've made lots of improvements, and we'd love to show you around!

Update your email preferences: {{email_preferences_url}}
Unsubscribe: {{unsubscribe_url}}""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>We Miss You! 👋</h1>
        </div>
        <div class="content">
            <p>Hi {{name}},</p>
            
            <p>It's been {{days_inactive}} days since you last visited Volera, and we've noticed some amazing deals you might be interested in!</p>
            
            <div class="highlight">
                <h3>What You've Missed</h3>
                <p>Price drops on items similar to your previous searches:</p>
                {{missed_deals}}
            </div>
            
            <div class="card" style="background-color: #FEF3C7; border-color: #F59E0B;">
                <h3>🎁 Special Welcome Back Offer</h3>
                {{special_offer}}
            </div>
            
            <a href="{{login_url}}" class="button">Return to Volera</a>
            
            <div class="card">
                <h3>Why Come Back?</h3>
                <ul class="list">
                    <li>New AI-powered price tracking</li>
                    <li>Improved deal alerts</li>
                    <li>Enhanced shopping experience</li>
                    <li>Exclusive member benefits</li>
                </ul>
            </div>
            
            <p>We've made lots of improvements, and we'd love to show you around!</p>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p><a href="{{email_preferences_url}}">Update Email Preferences</a> | <a href="{{unsubscribe_url}}">Unsubscribe</a></p>
        </div>
    """)
}

# Custom User Email Template
CUSTOM_USER_EMAIL = {
    "id": "8",
    "name": "Custom User Email",
    "subject": "{{subject}}",
    "description": "Template for sending personalized emails to specific users",
    "last_used": "2024-03-15",
    "available_variables": ["name", "subject", "message", "cta_text", "cta_url", "footer_note"],
    "content": """Dear {{name}},

{{message}}

{{cta_text}}: {{cta_url}}

Best regards,
The Volera Team

{{footer_note}}""",
    "html_content": BASE_TEMPLATE.format(content="""
        <div class="header">
            <h1>{{subject}}</h1>
        </div>
        <div class="content">
            <p>Dear {{name}},</p>
            
            <div class="highlight">
                {{message}}
            </div>
            
            <a href="{{cta_url}}" class="button">{{cta_text}}</a>
            
            <p>Best regards,<br>The Volera Team</p>
            
            <div class="card">
                <p>{{footer_note}}</p>
            </div>
        </div>
        <div class="footer">
            <p>© 2024 Volera. All rights reserved.</p>
            <p>This is a personalized message sent specifically to you.</p>
        </div>
    """)
}

BETA_LAUNCH_TEMPLATE = {
    "id": "volera_beta_launch",
    "name": "Volera Beta Launch",
    "subject": "🚀 Early Access: Volera Beta Launch on March 1!",
    "description": "Announces the early access launch of the Volera Beta to users.",
    "content": """
        >Hi {{name}},
        
        We're thrilled to announce that early access to the Volera Beta is launching on March 1 for our valued early adopters!

        🔥 What's New in the Beta
        ✅ Intelligent Product Discovery – Quickly find the best products tailored to your preferences.
        ✅ Real-Time Price Comparison – Compare prices across multiple retailers to get the best deal.
        ✅ Deal Tracking & Alerts – Get notified instantly when prices drop or new deals become available.
        ✅ Multi-Platform Integration – Access a wide range of products and deals from various online platforms—all in one place.
        ✅ User-Friendly Interface – Enjoy a seamless and intuitive browsing experience.
        ✅ Personalized Recommendations – Get tailored suggestions based on your browsing and purchase history.

        🎯 Quick Tips
        Make the most of Volera Beta by watching our short tutorial videos to get started.
        [Watch the Tutorials]

        We appreciate your support! Your feedback will help shape the future of Volera.

        Best regards,
        The Volera Team

        P.S. If you no longer wish to receive beta launch updates, you can [unsubscribe here].
        """,
    "html_content": BASE_TEMPLATE.format(content="""
        <p>Hi {{name}},</p>

        <p>We're thrilled to announce that early access to the Volera Beta is launching on March 1 for our valued early adopters!</p>

        <h3>🔥 What's New in the Beta</h3>
        <ul>
            <li>✅ Intelligent Product Discovery – Quickly find the best products tailored to your preferences.</li>
            <li>✅ Real-Time Price Comparison – Compare prices across multiple retailers to get the best deal.</li>
            <li>✅ Deal Tracking & Alerts – Get notified instantly when prices drop or new deals become available.</li>
            <li>✅ Multi-Platform Integration – Access a wide range of products and deals from various online platforms—all in one place.</li>
            <li>✅ User-Friendly Interface – Enjoy a seamless and intuitive browsing experience.</li>
            <li>✅ Personalized Recommendations – Get tailored suggestions based on your browsing and purchase history.</li>
        </ul>

        <h3>🎯 Quick Tips</h3>
        <p>Make the most of Volera Beta by watching our short tutorial videos to get started.</p>
        <p><a href="www.youtube.com/@volera1-v4i">Watch the Tutorials</a></p>

        <p>We appreciate your support! Your feedback will help shape the future of Volera.</p>

        <p>Best regards,<br>The Volera Team</p>

        <p>P.S. If you no longer wish to receive beta launch updates, you can <a href="#">unsubscribe here</a>.</p>
    """)
}

# Collection of all templates
EMAIL_TEMPLATES = {
    "welcome_email": WELCOME_EMAIL,
    "new_feature_announcement": NEW_FEATURE_ANNOUNCEMENT,
    "price_drop_alert": PRICE_DROP_ALERT,
    "monthly_summary": MONTHLY_SUMMARY,
    "support_reply": SUPPORT_REPLY,
    "newsletter": NEWSLETTER,
    "reengagement": REENGAGEMENT,
    "custom_user_email": CUSTOM_USER_EMAIL,
    "volera_beta_launch": BETA_LAUNCH_TEMPLATE
}

def get_email_template_by_id(template_id: str):
    """
    Retrieve an email template from EMAIL_TEMPLATES by its ID.
    """
    for template in EMAIL_TEMPLATES.values():
        if template.get("id") == template_id:
            return template
    return None

# "name": "Valued Customer",

DEFAULT_VARIABLES = {
    "dashboard_url": "https://volera.app/dashboard",
    "features": "No new features available at this time.",
    "tutorial_url": "https://volera.app/tutorials",
    "unsubscribe_url": "https://volera.app/unsubscribe",
    "items": "No items found.",
    "wishlist_url": "https://volera.app/wishlist",
    "manage_alerts_url": "https://volera.app/manage-alerts",
    "month": "This Month",
    "total_savings": "$0",
    "items_purchased": "0",
    "best_deal": "N/A",
    "tracked_items": "0",
    "alerts_count": "0",
    "avg_discount": "0%",
    "recommendations": "No recommendations available.",
    "email_preferences_url": "https://volera.app/email-preferences",
    "ticket_subject": "Your support ticket",
    "ticket_id": "0000",
    "response": "Thank you for your message. We will get back to you shortly.",
    "support_name": "Volera Support",
    "follow_up_date": "N/A",
    "support_portal_url": "https://volera.com/support",
    "faq_url": "https://volera.app/faq",
    "help_center_url": "https://volera.app/support",
    "community_url": "https://volera.app/community",
    "newsletter_title": "Volera Newsletter",
    "month_year": "Current Month, Current Year",
    "featured_deals": "No featured deals at this time.",
    "market_trends": "No market trends available.",
    "shopping_tips": "No shopping tips provided.",
    "trending_items": "No trending items.",
    "personalized_content": "No personalized recommendations.",
    "days_inactive": "N/A",
    "missed_deals": "No deals missed.",
    "special_offer": "No special offer available.",
    "login_url": "https://volera.app/login",
    "subject": "Message from Volera",
    "message": "No message content provided.",
    "cta_text": "Take Action",
    "cta_url": "https://volera.app",
    "footer_note": ""
}


