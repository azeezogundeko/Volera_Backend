from asyncio import gather, to_thread

from typing import Dict, List, Optional

from datetime import datetime
from .services import (
    get_user_growth_data, 
    get_daily_users_data, 
    get_error_rate_data, 
    get_date_logs,
    calculate_error_rate,
    generate_email_html
    )

from .email_templates import EMAIL_TEMPLATES, BASE_TEMPLATE, get_email_template_by_id
from .model import Contact, EmailConfig, AdminUsers, AppLog
from .email_manager import EmailManager
from .schema import AdminUserIn, EmailTemplatePreview, EmailTemplateResponse, SendEmailRequest
from ..auth.services import get_user_by_email, authenticate_user, create_access_token, split_name
from db import user_db

from utils.decorator import admin_required, super_admin_required
from utils.logging import logger
from utils.limiter import Limiter

from appwrite import query
from fastapi import APIRouter, Body, HTTPException, Request, Query
from fastapi.requests import Request

router = APIRouter()
# Send email using EmailManager
email_manager = EmailManager()

# Initialize rate limiter
limiter = Limiter()



@super_admin_required
@router.post("/create_admin")
async def create_admin_user(requests: Request, payload: AdminUserIn):
    user = get_user_by_email(payload.email)

    if user is None: 
        raise HTTPException(400, "User has not yet created an account")
    data = dict(
        is_super_admin=payload.super_admin,
        admin_email=payload.email,
        email_key=payload.email_key,
        is_editor=payload.editor,
        admin_password = ...
    )
    await AdminUsers.create(
        user.email, 
        data=data    
    )

    return data


@router.post("/login")
@limiter.limit(times=5, minutes=15)  # 5 attempts per 15 minutes per IP
async def admin_login(
    request: Request,
    email: str = Body(),
    password: str = Body()
):
    """
    Admin login endpoint with rate limiting protection against brute force attacks.
    Rate limits:
    - 5 attempts per 15 minutes per IP address
    - 3 attempts per 30 minutes per email address (handled in authenticate_user)
    
    This implements a dual-layer rate limiting strategy:
    1. IP-based limiting to prevent bulk attempts from a single source
    2. Email-based limiting to protect individual accounts from distributed attacks
    """
    try:
        user = await authenticate_user(request, email, password)

        if user is None:
            # Log failed attempt
            logger.warning(f"Failed login attempt for email: {email} from IP: {request.client.host}")
            raise HTTPException(401, "Invalid Credentials")

        try:
            await AdminUsers.read(user.id)
        except Exception as e:
            # Log unauthorized admin access attempt
            logger.warning(f"Unauthorized admin access attempt by user: {email} from IP: {request.client.host}")
            raise HTTPException(
                403,
                "Admin access required"
            )

        # Log successful login
        logger.info(f"Successful admin login for user: {email} from IP: {request.client.host}")
        
        access_token = create_access_token(data={"sub": email})
        
        return {
             "token": {"access_token": access_token, "token_type": "bearer"}
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during admin login: {str(e)}", exc_info=True)
        raise HTTPException(500, "Internal server error")


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


@router.get("/email/templates", response_model=List[EmailTemplateResponse])
@admin_required
async def get_email_templates(request: Request, include_preview: bool = False):
    """
    Get all available email templates.
    
    Args:
        request: FastAPI request object
        include_preview: If True, includes an HTML preview with sample data
    
    Returns:
        List[EmailTemplateResponse]: List of email templates formatted according to the interface
    """
    templates = []
    
    for template in EMAIL_TEMPLATES.values():
        # Extract variables from available_variables if present, otherwise provide empty list
        variables = template.get("available_variables", [])
        
        template_response = EmailTemplateResponse(
            id=template["id"],
            name=template["name"],
            subject=template["subject"],
            content=template["content"],  # Using the simple text content
            description=template["description"],
            last_used=template.get("last_used"),
            variables=variables,
            html_preview=template["html_content"] if include_preview else None
        )
        templates.append(template_response)
    
    # Sort templates by name for consistent ordering
    templates.sort(key=lambda x: x.name)
    
    return templates

@router.post("/email/preview")
@admin_required
async def preview_email_template(template: EmailTemplatePreview):
    """
    Generate HTML preview from simple text content with variable substitution.
    
    Args:
        template: EmailTemplatePreview object containing content and variables
    
    Returns:
        dict: Contains the generated HTML preview
    """
    try:
        # Replace variables in content
        content = template.content
        for var_name, var_value in template.variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", var_value)
        
        # Generate HTML
        html = generate_html_email(content)
        
        return {
            "success": True,
            "html": html
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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

@router.get("/users")
@admin_required
async def get_users(
    request: Request,
    page: int = Query(1, description="Page number", ge=1),
    limit: int = Query(50, description="Items per page", ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or email"),
    status: Optional[str] = Query(None, description="Filter by user status (active/inactive)"),
    sort: Optional[str] = Query(None, description="Sort field (created_at, email, status)")
) -> Dict:
    """
    Get all users with pagination, search, and filtering capabilities.
    
    Args:
        request: FastAPI request object
        page: Page number (1-based)
        limit: Number of items per page
        search: Optional search term for name or email
        status: Optional status filter
        sort: Optional sort field
    
    Returns:
        Dict containing users list, total count, and pagination info
    """
    try:
        # Build query filters
        queries = []
        
        # Add search filter
        if search:
            queries.append(
                query.Query.search("email", search)
            )
        
        # Add status filter
        if status:
            queries.append(
                query.Query.equal("status", status)
            )
            
        # Add sorting
        if sort:
            order = query.Query.ORDER_DESC if sort.startswith("-") else query.Query.ORDER_ASC
            sort_field = sort.lstrip("-")
            if sort_field in ["created_at", "email", "status"]:
                queries.append(query.Query.order_by(sort_field, order))
        else:
            # Default sort by creation date, newest first
            queries.append(query.Query.order_by("$createdAt", query.Query.ORDER_DESC))
        
        # Add pagination
        offset = (page - 1) * limit
        queries.extend([
            query.Query.limit(limit),
            query.Query.offset(offset)
        ])
        
        # Get total count first
        total = await User.count(queries[:-2])  # Exclude pagination queries
        
        # Get paginated results
        response = await User.list(queries)
        users = response.get("documents", [])
        
        # Clean sensitive data from user objects
        cleaned_users = []
        for user in users:
            user_dict = user.to_dict()
            # Remove sensitive fields
            user_dict.pop("password_hash", None)
            user_dict.pop("reset_token", None)
            cleaned_users.append(user_dict)
        
        return {
            "success": True,
            "data": {
                "users": cleaned_users,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit,  # Ceiling division
                "has_more": (page * limit) < total
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching users: {str(e)}"
        )



@router.post("/email/bulk/send")
@admin_required
async def send_users_email(
    request: Request,
    email_request: SendEmailRequest
):
    try:
        # Get users based on selection criteria
        users = []
        if email_request.emails:
            # Get specific users
            for email in email_request.emails:
                user = await get_user_by_email(email)
                if user is None:
                    continue   
                users.append(user.__dict__)
        else:
            user = await to_thread(user_db.list)
            users.extend(user["users"])
        if not users:
            raise HTTPException(
                status_code=400,
                detail="No users found matching the criteria"
            )
        if email_request.template_id is None:
            email_manager.send_bulk_email(
            subject=email_request.subject,
            content= BASE_TEMPLATE.format(email_request.content),
            emails=[email for user["email"] in users],
            account_key=email_request.account_key
            )
            return

        template = get_email_template_by_id(str(email_request.template_id))

        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )
        usernames = [split_name(user["name"])[0] for user in users]        
        
        result = email_manager.send_bulk_email(
            subject=email_request.subject,
            content= generate_email_html(email_request, template),
            emails=[user["email"] for user in users],
            usernames=usernames,
            account_key=email_request.account_key
        )

        return {
            "success": True,
            "message": f"Email sending queued for {len(users)} recipients",
            "data": {
                "task_id": result["task_id"],
                "recipients_count": len(users)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error queueing emails: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error queueing emails: {str(e)}"
        )
