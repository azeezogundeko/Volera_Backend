from celery import Celery
from typing import List, Dict, Optional, Union, Literal
import smtplib
from typing import Dict, List
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time
from pathlib import Path

from utils.logging import logger
from utils.email_manager import manager as email_manager

# Initialize Celery with multiple queues
celery_app = Celery('volera',
                    broker='redis://redis:6379/0',
                    backend='redis://redis:6379/0')

# Configure Celery with priority queues
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_queues={
        'high_priority': {'routing_key': 'high_priority'},
        'default': {'routing_key': 'default'},
        'low_priority': {'routing_key': 'low_priority'}
    },
    task_routes={
        'send_email': {'queue': 'default'},
        'send_bulk_email': {'queue': 'low_priority'}
    }
)

# Rate limiting settings
RATE_LIMIT = {
    'emails_per_minute': 3,  # Adjust based on your SMTP provider's limits
    'burst_size': 50
}

# Priority settings
PRIORITY_SETTINGS = {
    'high': {
        'queue': 'high_priority',
        'retry_delay': 30,  # 30 seconds
        'max_retries': 5
    },
    'normal': {
        'queue': 'default',
        'retry_delay': 60,  # 1 minute
        'max_retries': 3
    },
    'low': {
        'queue': 'low_priority',
        'retry_delay': 300,  # 5 minutes
        'max_retries': 2
    }
}

@celery_app.task(name="send_email", bind=True, max_retries=3, rate_limit='100/m')
def send_email(self,
                to_email: str,
                subject: str,
                html_content: str,
                from_name: Optional[str] = None,
                account_key: str = "no-reply",
                bcc: Optional[List[str]] = None,
                attachments: Optional[List[Dict[str, Union[str, bytes]]]] = None,
                priority: Literal['high', 'normal', 'low'] = 'normal') -> Dict:
    """
    Celery task to send emails asynchronously with priority handling.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email
        from_name: Optional sender name override
        account_key: Email account to use (default: "no-reply")
        bcc: Optional list of BCC recipients
        attachments: Optional list of attachment dictionaries
        priority: Email priority level ('high', 'normal', 'low')

    Returns:
        Dict with status and message
    """
    # Get priority settings
    priority_config = PRIORITY_SETTINGS[priority]
    
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

        logger.info(f"[{priority.upper()} PRIORITY] Email sent successfully to {to_email}" + 
                   (f" with {len(bcc)} BCC recipients" if bcc else ""))
        return {
            "status": "success", 
            "message": "Email sent successfully",
            "recipient": to_email,
            "bcc_count": len(bcc) if bcc else 0,
            "priority": priority
        }

    except Exception as e:
        error_msg = f"Error sending {priority} priority email to {to_email}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Determine if we should retry based on the error type
        should_retry = isinstance(e, (smtplib.SMTPServerDisconnected, 
                                    smtplib.SMTPSenderRefused,
                                    smtplib.SMTPResponseException,
                                    ConnectionError))
        
        if should_retry and self.request.retries < priority_config['max_retries']:
            retry_count = self.request.retries
            retry_delay = priority_config['retry_delay'] * (2 ** retry_count)
            raise self.retry(exc=e, countdown=retry_delay)
        
        return {
            "status": "error",
            "message": error_msg,
            "recipient": to_email,
            "priority": priority
        }




def substitute_variables(template: str, variables: Dict[str, str], user_name: str = None) -> str:
    """
    Replaces placeholders in the template with actual values from the variables dictionary.
    If user_name is provided, it substitutes {name} with the given user name.
    """
    def replacer(match):
        key = match.group(1)
        if key == "name" and user_name:
            return user_name
        return variables.get(key, f"{{{{{key}}}}}")  # Keep placeholder if not found
    
    return re.sub(r"{{(\w+)}}", replacer, template)

@celery_app.task(name="send_bulk_email")
def send_bulk_email(emails: List[str],
                    user_names: List[str],
                    subject: str,
                    html_content: str,
                    from_name: Optional[str] = None,
                    account_key: str = "no-reply",
                    attachments: Optional[List[Dict[str, Union[str, bytes]]]] = None,
                    priority: Literal['high', 'normal', 'low'] = 'low') -> Dict:
    """
    Celery task to send bulk emails with rate limiting and priority handling.

    Args:
        emails: List of recipient email addresses
        user_names: List of recipient names
        subject: Email subject
        html_content: HTML content of the email
        from_name: Optional sender name override
        account_key: Email account to use (default: "no-reply")
        attachments: Optional list of attachments to include
        priority: Priority level for the bulk emails

    Returns:
        Dict with status and task IDs
    """
    results = []
    chunk_size = min(RATE_LIMIT['burst_size'], RATE_LIMIT['emails_per_minute'])
    
    # Split email list and names into chunks
    email_chunks = [emails[i:i + chunk_size] for i in range(0, len(emails), chunk_size)]
    name_chunks = [user_names[i:i + chunk_size] for i in range(0, len(user_names), chunk_size)]
    
    # Send emails in chunks with rate limiting
    for i, (chunk, name_chunk) in enumerate(zip(email_chunks, name_chunks)):
        # Add delay between chunks to respect rate limits
        if i > 0:
            time.sleep(60 / RATE_LIMIT['emails_per_minute'] * chunk_size)
        
        chunk_tasks = [
            send_email.apply_async(
                args=[
                    email,
                    subject,
                    substitute_variables(html_content, {}, user_name),
                    from_name,
                    account_key
                ],
                kwargs={
                    'attachments': attachments,
                    'priority': priority
                },
                queue=PRIORITY_SETTINGS[priority]['queue']
            )
            for email, user_name in zip(chunk, name_chunk)
        ]
        results.extend(chunk_tasks)
        
        logger.info(f"[{priority.upper()} PRIORITY] Initiated sending chunk {i+1}/{len(email_chunks)} " +
                   f"({len(chunk)} emails)")

    return {
        "status": "success",
        "message": f"Bulk email task initiated for {len(emails)} recipients",
        "task_ids": [str(task.id) for task in results],
        "total_chunks": len(email_chunks),
        "chunk_size": chunk_size,
        "priority": priority
    }
