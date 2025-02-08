import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from .model import EmailConfig, User, EmailTemplate

class EmailManager:
    def __init__(self):
        self._config = None
        self._smtp = None

    async def initialize(self):
        """Initialize email configuration"""
        self._config = await EmailConfig.get_current_config()
        if not self._config:
            raise ValueError("Email configuration not found")

    async def connect(self):
        """Connect to SMTP server"""
        if not self._config:
            await self.initialize()
        
        self._smtp = smtplib.SMTP(self._config["smtp_host"], self._config["smtp_port"])
        self._smtp.starttls()
        self._smtp.login(self._config["smtp_user"], self._config["smtp_password"])

    async def close(self):
        """Close SMTP connection"""
        if self._smtp:
            self._smtp.quit()
            self._smtp = None

    async def send_bulk_email(self, subject: str, content: str, recipient_filter: str) -> Dict:
        """Send bulk emails to filtered recipients"""
        try:
            await self.connect()
            
            # Get filtered users
            users = await User.get_filtered_users(recipient_filter)
            
            sent_count = 0
            failed_count = 0
            
            # Create template instance
            template = EmailTemplate()
            
            for user in users:
                try:
                    # Replace placeholders in content
                    personalized_content = content.replace("{{name}}", user.get("name", ""))
                    
                    # Compose full HTML email
                    html_content = template.compose_email(subject, personalized_content, user["email"])
                    
                    msg = MIMEMultipart('alternative')
                    msg["From"] = f"{self._config['from_name']} <{self._config['from_email']}>"
                    msg["To"] = user["email"]
                    msg["Subject"] = subject
                    
                    # Attach both plain text and HTML versions
                    text_part = MIMEText(personalized_content.strip(), 'plain')
                    html_part = MIMEText(html_content.strip(), 'html')
                    
                    msg.attach(text_part)
                    msg.attach(html_part)
                    
                    self._smtp.send_message(msg)
                    sent_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    # Log the error
                    print(f"Failed to send email to {user['email']}: {str(e)}")
            
            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count
            }
            
        finally:
            await self.close()

     

    


