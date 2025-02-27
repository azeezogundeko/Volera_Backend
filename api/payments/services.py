import pytz
from datetime import datetime

from.model import DailyUsage

# from utils.emails import send_email
from utils.email_manager import manager
from utils.email_templates.payment_acknowledgement import generate_credit_purchase_email
from utils.logging import logger

from utils.celery_tasks import send_email

from fastapi import BackgroundTasks
from appwrite.exception import AppwriteException



def send_payment_acknowledgement(user_name, email, reference, amount, credits, payment_method):
    html_content = generate_credit_purchase_email(user_name, reference, amount, credits, payment_method)
    send_email.delay(
        to_email=email,
        subject="Payment Acknowledgement - Volera",
        html_content=html_content,
        priority='high'
    )


async def check_daily_limit(user_id: str, current_time: datetime, daily_limit: int) -> bool:
    """
    Check if a user is within their daily credit limit.
    
    :param user_id: The user's ID.
    :param current_time: The current UTC time.
    :param daily_limit: The daily limit.
    :return: True if the action is allowed, False if it would exceed the limit.
    """
    from db import user_db
    user = await user_db.get(user_id)
    user_timezone = user.custom_metadata.get("timezone") if user.custom_metadata else "UTC"
    tz = pytz.timezone(user_timezone)
    local_time = current_time.astimezone(tz)
    day_str = local_time.strftime("%Y-%m-%d")
    document_id = f"{user_id}_{day_str}"
    
    try:
        daily_doc = await DailyUsage.read(document_id)
        current_total = daily_doc.total_credits
    except AppwriteException:
        # If no document exists, then total is zero.
        current_total = 0

    # For example, if adding more credits (e.g., spending 3 credits) would exceed the daily limit:
    if current_total + 3 > daily_limit:
        return False
    return True
