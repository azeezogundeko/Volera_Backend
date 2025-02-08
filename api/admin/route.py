from asyncio import gather

from fastapi import APIRouter, Body, HTTPException
from fastapi.requests import Request
from typing import Dict
from datetime import datetime, timedelta
from .services import (
    get_user_growth_data, 
    get_daily_users_data, 
    get_error_rate_data, 
    get_date_logs,
    calculate_error_rate
    )

from .model import Contact, EmailConfig, EmailTemplate, DailyLog, MonthlyLog, AppLog
from .email_manager import EmailManager

from utils.decorator import admin_required
from utils.logging import logger

from appwrite import query

router = APIRouter()

@router.post("/contact")
async def save_contact(
    name: str = Body(),
    email: str = Body(),
    message: str = Body()
): 
    
    await Contact.create(Contact.get_unique_id(), 
        dict(
            name=name, email=email, message=message
        )
    )

    return {"message": "success"}

@admin_required
@router.get("/system-log")

@router.post("/email/bulk")
async def send_bulk_email(
    subject: str = Body(),
    content: str = Body(),
    recipient_filter: str = Body()
):
    try:
        email_manager = EmailManager()
        result = await email_manager.send_bulk_email(subject, content, recipient_filter)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/email/config")
async def get_email_config() -> Dict:
    """Get current email configuration"""
    config = await EmailConfig.get_current_config()
    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")
    
    # Remove sensitive information
    safe_config = {
        "from_email": config["from_email"],
        "from_name": config["from_name"]
    }
    return safe_config

@router.get("/email/templates")
async def get_email_templates():
    """Get all available email templates"""
    try:
        templates = EmailTemplate.get_default_templates()
        return {
            "success": True,
            "templates": templates
        }
    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# @admin_required
@router.get("/stats")
async def get_dashboard_stats():
    """Get dashboard statistics from daily and monthly logs"""
    try:
        # First, await get_date_logs() to obtain the list of date log results
        date_logs = await get_date_logs()
        print(date_logs)
        
        # Then, run all tasks concurrently including the already-awaited date_logs
        results = await gather(
            Contact.list([query.Query.equal("acknowledged", False)]),
            AppLog.get_or_create("engr_ogundeko_volera"),
        )
        
        messages, system_app = results

        today_stats, yesterday_stats, current_month_stats, last_month_stats = date_logs

        # Calculate core metrics
        today_error_rate = calculate_error_rate(today_stats)
        revenue = {
            "today": today_stats.total_revenue_generated,
            "thisMonth": current_month_stats.total_revenue_generated,
            "total": system_app.total_revenue_generated
        }

        return {
            "success": True,
            "stats": {
                "revenue": revenue,
                "totalUsers": current_month_stats.total_users,
                "newUsers": today_stats.total_users,
                "newTransactions": today_stats.no_of_transactions,
                "errorRate": round(today_error_rate, 2),
                "totalTransactions": current_month_stats.no_of_transactions,
                "activeUsers": current_month_stats.total_active_users,
                "inactiveUsers": current_month_stats.total_inactive_users,
                "totalMessages": messages["total"]
            }
        }
    except Exception as e:
        logger.error(str(e), exc_info=True)
        return {"success": False, "error": str(e)}

# Helper functions



# @admin_required
@router.get("/charts")
async def get_dashboard_graphs():
    """Get graph data for dashboard visualizations"""
    try:
        today = datetime.now()
        
        # Get data for user growth (last 6 months)
        user_growth_data = await get_user_growth_data(today)
        
        # Get data for daily new users (last 7 days)
        daily_users_data = await get_daily_users_data(today)
        
        # Get data for error rate (last 7 days)
        error_rate_data = await get_error_rate_data(today)
        
        return {
            "success": True,
            "data": {
                "userGrowth": user_growth_data,
                "dailyNewUsers": daily_users_data,
                "errorRate": error_rate_data
            }
        }
        
    except Exception as e:
        logger.error(str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
