from typing import Dict, Optional, List
from datetime import datetime, timedelta
from asyncio import to_thread
import re
from typing import Literal
import calendar

from asyncio import gather
from .schema import SendEmailRequest

from .model import DailyLog, MonthlyLog, AppLog
from utils.celery_tasks import send_email, send_bulk_email
from .email_templates import DEFAULT_VARIABLES
from db import user_db

from appwrite.query import Query



def substitute_default_variables(content: str, variables: Dict[str, str]) -> str:
    """
    Substitute any remaining placeholders in the content with default values.
    The provided variables (if any) override the defaults.
    """
    # Merge default variables with provided ones (provided ones take precedence)
    merged_vars = {**DEFAULT_VARIABLES, **variables}
    
    def replacer(match):
        var_name = match.group(1)
        return str(merged_vars.get(var_name, match.group(0)))
    
    # This regex matches placeholders like {{ variable_name }} (with optional spaces)
    return re.sub(r"{{\s*(\w+)\s*}}", replacer, content)

def substitute_variables(template: str, variables: Dict[str, str]) -> str:
    """
    Substitute placeholders in the template using only the provided variables.
    If a variable is missing, the placeholder remains intact.
    """
    def replacer(match):
        key = match.group(1)
        return variables.get(key, f"{{{{{key}}}}}")
    
    return re.sub(r"{{(\w+)}}", replacer, template)

def generate_email_html(request: 'SendEmailRequest', template: Dict[str, str]) -> str:
    """
    Generates the final HTML content by first substituting provided variables.
    If any placeholders remain, default values are substituted in a second pass.
    """
    variables = request.variables or {}
    
    # First, substitute only provided variables.
    content = substitute_variables(template["html_content"], variables)
    
    # If placeholders still exist in the content, substitute defaults.
    if re.search(r"{{\s*(\w+)\s*}}", content):
        # We pass an empty dict here because provided variables were already applied.
        content = substitute_default_variables(content, {})
    
    return content

async def get_user_growth_data(today: datetime) -> Dict:
    """Get monthly user growth data for the last 6 months"""
    months_data = {"labels": [], "data": []}
    
    for i in range(5, -1, -1):  # Last 6 months
        # Calculate target month
        target_date = today.replace(day=1) - timedelta(days=1)  # Last day of previous month
        target_date = target_date.replace(day=1)  # First day of that month
        target_date = target_date - timedelta(days=30*i)  # Go back i months
        
        month_str = target_date.strftime("%Y-%m")
        month_name = target_date.strftime("%b")  # Short month name
        
        # Get monthly stats
        monthly_stats = await MonthlyLog.get_or_create(month_str)
        
        months_data["labels"].append(month_name)
        months_data["data"].append(monthly_stats.total_users)
    
    return months_data

async def get_daily_users_data(today: datetime) -> Dict:
    """Get daily new users data for the last 7 days"""
    days_data = {"labels": [], "data": []}
    
    for i in range(6, -1, -1):  # Last 7 days
        target_date = today - timedelta(days=i)
        day_str = target_date.strftime("%Y-%m-%d")
        day_name = target_date.strftime("%a")  # Short day name
        
        # Get daily stats
        daily_stats = await DailyLog.get_or_create(day_str)
        
        days_data["labels"].append(day_name)
        days_data["data"].append(daily_stats.total_users)
    
    return days_data

async def get_error_rate_data(today: datetime) -> Dict:
    """Get daily error rate data for the last 7 days"""
    error_data = {"labels": [], "data": []}
    
    for i in range(6, -1, -1):  # Last 7 days
        target_date = today - timedelta(days=i)
        day_str = target_date.strftime("%Y-%m-%d")
        day_name = target_date.strftime("%a")  # Short day name
        
        # Get daily stats
        daily_stats = await DailyLog.get_or_create(day_str)
        
        # Calculate error rate
        error_rate = 0
        if daily_stats.no_of_transactions > 0:
            error_rate = round((daily_stats.no_of_errors / daily_stats.no_of_transactions) * 100, 1)
        
        error_data["labels"].append(day_name)
        error_data["data"].append(error_rate)
    
    return error_data

async def get_date_logs():
    now = datetime.now()
    dates = {
        "today": now.strftime("%Y-%m-%d"),
        "yesterday": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
        "current_month": now.strftime("%Y-%m"),
        "last_month": (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
    }
    return await gather(
        DailyLog.get_or_create(dates["today"]),
        DailyLog.get_or_create(dates["yesterday"]),
        MonthlyLog.get_or_create(dates["current_month"]),
        MonthlyLog.get_or_create(dates["last_month"])
    )

def calculate_error_rate(stats):
    if stats.no_of_transactions > 0:
        return (stats.no_of_errors / stats.no_of_transactions) * 100
    return 0.0

async  def system_log(type: Literal["user", "error", "active", "inactive", "transaction"], amount=None) -> None:
    """
    Update system log for at the provided timestamp.
    
    """
    from asyncio import gather
    
    await gather(DailyLog.update_log(type, amount), MonthlyLog.update_log(type, amount), AppLog.update_log(type, amount))

async def send_user_email(to_email: str, subject: str, html_content: str, from_name: Optional[str] = None):
    """Send an email to a single user using Celery."""
    task = send_email.delay(to_email, subject, html_content, from_name)
    return {"task_id": str(task.id)}

async def send_bulk_user_email(emails: List[str], subject: str, html_content: str, from_name: Optional[str] = None):
    """Send emails to multiple users using Celery."""
    result = await send_bulk_email.delay(emails, subject, html_content, from_name)
    return {
        "status": "success",
        "message": f"Bulk email task initiated for {len(emails)} recipients",
        "task_id": str(result.id)
    }

async def get_all_users(queries: Optional[List] = None) -> Dict:
    """
    Get all users with pagination support.
    
    Args:
        limit (int): Number of users per page (default: 25)
        offset (int): Number of users to skip (default: 0)
        queries (List, optional): Additional query parameters for filtering
    
    Returns:
        Dict: Contains list of users and total count
            {
                "users": List[Dict],
                "total": int
            }
    """
    try:

        
         
        # Get paginated users
        users_response = await to_thread(user_db.list, queries)
        
        return {
            "users": users_response.get("users", []),
            "total": len(users_response.get("users", []))
        }
        
    except Exception as e:
        # Log the error and re-raise
        raise Exception(f"Failed to fetch users: {str(e)}")