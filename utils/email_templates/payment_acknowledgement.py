import datetime

def generate_credit_purchase_email(user_name, order_id, amount_paid, credits_awarded, payment_method):
    return f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
                
                @media screen and (max-width: 600px) {{
                    .container {{
                        padding: 1.5rem !important;
                    }}
                    .transaction-grid {{
                        grid-template-columns: 1fr !important;
                        gap: 0.5rem !important;
                    }}
                    .transaction-label {{
                        color: #6b7280 !important;
                        font-size: 0.875rem !important;
                        margin-bottom: 0.125rem !important;
                    }}
                    .transaction-value {{
                        font-size: 1rem !important;
                        padding-bottom: 0.75rem !important;
                        margin-bottom: 0.75rem !important;
                        border-bottom: 1px solid #e5e7eb !important;
                    }}
                    .transaction-value:last-child {{
                        border-bottom: none !important;
                        margin-bottom: 0 !important;
                        padding-bottom: 0 !important;
                    }}
                    .button {{
                        width: 100% !important;
                    }}
                }}
            </style>
        </head>
        <body style="font-family: 'Inter', sans-serif; background-color: #f5f5f5; color: #1a1a1a; padding: 1rem; margin: 0;">
            <div class="container" style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 0.75rem; padding: 2.5rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                <div style="text-align: center; margin-bottom: 2.5rem;">
                    <h1 style="font-size: 1.5rem; font-weight: 600; color: #10b981; margin: 0;">
                        Payment Confirmation
                    </h1>
                    <p style="color: #6b7280; margin-top: 0.5rem; font-size: 0.875rem;">
                        Thank you for your purchase
                    </p>
                </div>

                <div style="margin-bottom: 2rem;">
                    <p style="color: #374151; line-height: 1.5;">Dear {user_name},</p>
                    <p style="color: #374151; line-height: 1.5;">Thank you for purchasing Volera credits. Your payment has been processed successfully, and your credits have been added to your account.</p>
                </div>

                <div style="background-color: #f8fafc; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 2rem;">
                    <h2 style="font-size: 1.125rem; font-weight: 600; color: #10b981; margin-bottom: 1.25rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e5e7eb;">Transaction Details</h2>
                    
                    <div class="transaction-grid" style="display: grid; grid-template-columns: 1fr 2fr; gap: 1rem; color: #4b5563;">
                        <div class="transaction-label" style="font-weight: 500;">Transaction ID:</div>
                        <div class="transaction-value" style="color: #111827;">{order_id}</div>
                        
                        <div class="transaction-label" style="font-weight: 500;">Date:</div>
                        <div class="transaction-value" style="color: #111827;">{datetime.datetime.now().strftime("%B %d, %Y %H:%M")}</div>
                        
                        <div class="transaction-label" style="font-weight: 500;">Amount Paid:</div>
                        <div class="transaction-value" style="color: #111827;">₦{amount_paid:,.2f}</div>
                        
                        <div class="transaction-label" style="font-weight: 500;">Credits Added:</div>
                        <div class="transaction-value" style="color: #111827;">{credits_awarded:,} credits</div>
                        
                        <div class="transaction-label" style="font-weight: 500;">Payment Method:</div>
                        <div class="transaction-value" style="color: #111827;">{payment_method}</div>
                    </div>
                </div>

                <div style="text-align: center; margin-top: 2.5rem;">
                    <a href="https://volera.app/dashboard" class="button" style="display: inline-block; background-color: #10b981; color: white; padding: 0.875rem 2rem; border-radius: 0.5rem; text-decoration: none; font-weight: 500; transition: background-color 0.2s; max-width: 100%; width: 200px; box-sizing: border-box;">
                        View Dashboard
                    </a>
                </div>

                <div style="margin-top: 2.5rem; border-top: 1px solid #e5e7eb; padding-top: 2rem;">
                    <div style="text-align: center;">
                        <p style="color: #6b7280; font-size: 0.875rem; margin-bottom: 0.5rem;">If you have any questions, please contact our support team</p>
                        <a href="mailto:support@volera.app" style="color: #10b981; text-decoration: none; font-size: 0.875rem; font-weight: 500;">support@volera.app</a>
                    </div>
                    <p style="color: #9ca3af; font-size: 0.75rem; text-align: center; margin-top: 1.5rem;">{datetime.datetime.now().year} Volera. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """