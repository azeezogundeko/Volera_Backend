# Build the HTML email content
def get_payment_acknowlegement(reference, amount, credits):
    return f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Payment Successful - Volera</title>
        <style>
        body {{
            background-color: #0a0a0a;
            color: white;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }}
        .container {{
            width: 100%;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .card {{
            background-color: #111111;
            border: 1px solid #333;
            border-radius: 10px;
            overflow: hidden;
        }}
        .header {{
            text-align: center;
            padding: 20px;
        }}
        .header img {{
            display: block;
            margin: 0 auto;
            width: 64px;
            height: 64px;
        }}
        .header h1 {{
            font-size: 24px;
            margin: 10px 0;
            background: linear-gradient(to right, white, #2ed573);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .content {{
            text-align: center;
            padding: 20px;
        }}
        .content p {{
            font-size: 16px;
            line-height: 1.5;
        }}
        .receipt {{
            background-color: #0c0c0c;
            border: 1px solid #555;
            border-radius: 8px;
            padding: 10px;
            margin: 20px auto;
            max-width: 90%;
            font-size: 14px;
            text-align: left;
        }}
        .receipt p {{
            margin: 5px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 14px;
        }}
        .footer a {{
            color: #2ed573;
            text-decoration: none;
        }}
        </style>
    </head>
    <body>
        <div class="container">
        <div class="card">
            <div class="header">
            <!-- You can replace the image src with your own logo or icon -->
            <img src="https://via.placeholder.com/64/2ed573/ffffff?text=✓" alt="Success">
            <h1>Payment Successful!</h1>
            </div>
            <div class="content">
            <p>Thank you for purchasing credits on <strong>Volera</strong>.</p>
            <p>Your credits have been added successfully.</p>
            <div class="receipt">
                <p><strong>Transaction Reference:</strong> {reference}</p>
                <p><strong>Amount:</strong> ${amount:.2f}</p>
                <p><strong>Credits:</strong> {credits}</p>
            </div>
            </div>
            <div class="footer">
            <p>
                Visit your <a href="https://voleraai.com/dashboard">dashboard</a> for more details.
            </p>
            </div>
        </div>
        </div>
    </body>
    </html>
    """
