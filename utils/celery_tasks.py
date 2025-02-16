from celery import Celery
from typing import List, Dict, Optional, Union
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from pathlib import Path

from utils.logging import logger
from utils.email_manager import manager as email_manager

# Initialize Celery
celery_app = Celery('volera',
                    broker='redis://redis:6379/0',
                    backend='redis://redis:6379/0')

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Rate limiting settings
RATE_LIMIT = {
    'emails_per_minute': 3,  # Adjust based on your SMTP provider's limits
    'burst_size': 50
}

@celery_app.task(name="send_email", bind=True, max_retries=3, rate_limit='100/m')
def send_email(self,
                to_email: str,
                subject: str,
                html_content: str,
                from_name: Optional[str] = None,
                account_key: str = "no-reply",
                bcc: Optional[List[str]] = None,
                attachments: Optional[List[Dict[str, Union[str, bytes]]]] = None) -> Dict:
    """
    Celery task to send emails asynchronously.
    Includes retry logic with exponential backoff.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        from_name: Optional sender name override
        account_key: Email account to use (default: "no-reply")
        bcc: Optional list of BCC recipients
        attachments: Optional list of attachment dictionaries with format:
                    [{'filename': 'name.pdf', 'content': bytes_content}]

    Returns:
        Dict with status and message
    """
    try:
        # Choose the email account to use
        email_manager.choose_account(account_key)
        
        # Send the email using the manager
        email_manager.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            recipients=bcc,
            attachments=attachments
        )

        logger.info(f"Email sent successfully to {to_email}" + 
                   (f" with {len(bcc)} BCC recipients" if bcc else ""))
        return {
            "status": "success", 
            "message": "Email sent successfully",
            "recipient": to_email,
            "bcc_count": len(bcc) if bcc else 0
        }

    except Exception as e:
        error_msg = f"Error sending email to {to_email}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Determine if we should retry based on the error type
        should_retry = isinstance(e, (smtplib.SMTPServerDisconnected, 
                                    smtplib.SMTPSenderRefused,
                                    smtplib.SMTPResponseException,
                                    ConnectionError))
        
        if should_retry and self.request.retries < self.max_retries:
            retry_count = self.request.retries
            max_retry_delay = 300  # 5 minutes
            retry_delay = min(60 * (2 ** retry_count), max_retry_delay)
            raise self.retry(exc=e, countdown=retry_delay)
        
        return {
            "status": "error",
            "message": error_msg,
            "recipient": to_email
        }

@celery_app.task(name="send_bulk_email")
def send_bulk_email(emails: List[str],
                   subject: str,
                   html_content: str,
                   from_name: Optional[str] = None,
                   account_key: str = "no-reply",
                   attachments: Optional[List[Dict[str, Union[str, bytes]]]] = None) -> Dict:
    """
    Celery task to send bulk emails with rate limiting.
    Breaks the email list into chunks and sends them in parallel.

    Args:
        emails: List of recipient email addresses
        subject: Email subject
        html_content: HTML content of the email
        from_name: Optional sender name override
        account_key: Email account to use (default: "no-reply")
        attachments: Optional list of attachments to include

    Returns:
        Dict with status and task IDs
    """
    results = []
    chunk_size = min(RATE_LIMIT['burst_size'], RATE_LIMIT['emails_per_minute'])
    
    # Split email list into chunks
    email_chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
    
    # Send emails in chunks with rate limiting
    for i, chunk in enumerate(email_chunks):
        # Add delay between chunks to respect rate limits
        if i > 0:
            time.sleep(60 / RATE_LIMIT['emails_per_minute'] * chunk_size)
        
        chunk_tasks = [
            send_email.delay(
                email,
                subject,
                html_content,
                from_name,
                account_key,
                attachments=attachments
            )
            for email in chunk
        ]
        results.extend(chunk_tasks)
        
        logger.info(f"Initiated sending chunk {i+1}/{len(email_chunks)} " +
                   f"({len(chunk)} emails)")

    return {
        "status": "success",
        "message": f"Bulk email task initiated for {len(emails)} recipients",
        "task_ids": [str(task.id) for task in results],
        "total_chunks": len(email_chunks),
        "chunk_size": chunk_size
    } 