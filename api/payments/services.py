import pytz
from datetime import datetime
from asyncio import to_thread

from db import user_db
from.model import DailyUsage
# from utils.emails import send_email
from utils.email_manager import manager
from utils.email_templates.payment_acknowledgement import generate_credit_purchase_email

from fastapi import BackgroundTasks
from appwrite.exception import AppwriteException



def send_payment_acknowledgement(user_name, email, reference, amount, credits, payment_method, b: BackgroundTasks):
    manager.choose_account("no-reply")
    html_content = generate_credit_purchase_email(user_name, reference, amount, credits, payment_method)
    b.add_task(manager.send_email, email, "Payment Acknowledgement - Volera", html_content)


async def record_credit_transaction(user_id, delta: int, created_at: datetime = datetime.now()) -> None:
    """
    Record a credit transaction and update daily and monthly usage.

    :param user_id: The user's ID.
    :param delta: The credit delta (positive or negative).
    :param created_at: The timestamp (UTC) of the transaction.
    """
    user = await to_thread(user_db.get, user_id) 
    user_timezone = user["prefs"].get("timezone") if user["prefs"] else "UTC"
    # Optionally: Insert a transaction document to record the individual event.
    # from transaction_model import Transaction  # if you have one
    # transaction_data = {
    #     "user_id": user_id,
    #     "amount": delta,
    #     "created_at": created_at.isoformat(),
    #     # ... additional fields
    # }
    # await Transaction.create(Transaction.get_unique_id(), transaction_data)
    
    # Update daily and monthly usage documents.
    await DailyUsage.update_usage(user_id, created_at, delta, user_timezone)
    # await MonthlyUsage.update_usage(user_id, created_at, delta, user_timezone)


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
