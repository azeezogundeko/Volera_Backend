import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from email.mime.application import MIMEApplication

from dotenv import load_dotenv

load_dotenv()


smtp_password = os.getenv("SMTP_PASSWORD")
SOLVEBYTE_FROM_EMAIL = os.environ.get("FROM_EMAIL")
from_email = "azeezogundeko@volera.app"
smtp_server = "smtp.gmail.com"
smtp_port = 465

class EmailAccount:
    """
    Represents an email account with its configuration.
    """
    def __init__(self, name, from_email, smtp_password, smtp_server="smtp.gmail.com", smtp_port=465):
        self.name = name  # e.g., "Azeez"
        self.from_email = from_email  # e.g., "azeezogundeko@volera.app"
        self.smtp_password = smtp_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def display_name(self):
        """
        Returns a formatted display name.
        """
        return self.name


class EmailAccountManager:
    """
    Manages multiple email accounts and sending emails using the selected account.
    """
    def __init__(self):
        # Initialize your accounts. Credentials can be loaded from environment variables or hardcoded.
        self.accounts = {
            "azeez_volera": EmailAccount(
                name="Azeez from Volera",
                from_email=os.environ.get("FROM_AZEEZ_EMAIL"),
                smtp_password=os.getenv("SMTP_PASSWORD")
            ),
            "solvebyte": EmailAccount(
                name="Solvebyte",
                from_email=os.environ.get("FROM_EMAIL"),
                smtp_password=os.getenv("SMTP_PASSWORD")
            )
        }
        self.current_account = None

    def choose_account(self, account_key):
        """
        Chooses an account by key (e.g., 'volera' or 'solvebyte').
        """
        if account_key in self.accounts:
            self.current_account = self.accounts[account_key]
            print(f"Using account: {self.current_account.display_name()} <{self.current_account.from_email}>")
        else:
            raise ValueError(f"Account '{account_key}' not found.")
        return self.current_account

    def send_email(self, to_email, subject, html_content, attachments=None, recipients=None):
        """
        Sends an email using the selected account.
        """
        if not self.current_account:
            raise ValueError("No email account selected. Please choose an account using choose_account().")
        
        # Create the email message
        message = MIMEMultipart("alternative")
        message["To"] = to_email
        message["Subject"] = subject
        message["From"] = f"{self.current_account.display_name()} <{self.current_account.from_email}>"
        if recipients:
            message["Bcc"] = ", ".join(recipients)
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid(domain=self.current_account.from_email.split("@")[1])
        message["MIME-Version"] = "1.0"
        message["X-Priority"] = "3"  # Normal priority
        message["X-Mailer"] = "Python Email Client"
        message["Reply-To"] = self.current_account.from_email
        message["Return-Path"] = self.current_account.from_email

        # Attach the HTML content
        message.attach(MIMEText(html_content, "html"))

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                filename = attachment.filename
                try:
                    attachment_data = attachment.file.read()
                except Exception as e:
                    print(f"Error reading attachment: {e}")
                    continue  # Skip this attachment on error
                attachment_mime = MIMEApplication(attachment_data)
                attachment_mime.add_header("Content-Disposition", f"attachment; filename={filename}")
                message.attach(attachment_mime)

        # Connect to the SMTP server and send the message
        try:
            with smtplib.SMTP_SSL(self.current_account.smtp_server, self.current_account.smtp_port) as smtp:
                smtp.login(self.current_account.from_email, self.current_account.smtp_password)
                smtp.send_message(message)
                print(f"Email sent to {to_email} from {self.current_account.from_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")
            raise

manager = EmailAccountManager()
# ===== Usage Example =====

if __name__ == "__main__":
    # Initialize the manager
    manager = EmailAccountManager()
    
    # Choose which account to use
    manager.choose_account("volera")  # Or "solvebyte" if you prefer

    # Define email details
    recipient_email = "recipient@example.com"
    subject = "Your Volera Waitlist Spot is Reserved ✅"
    html_content = "<p>Thank you for joining the waitlist!</p>"
    
    # Send the email
    manager.send_email(recipient_email, subject, html_content)
