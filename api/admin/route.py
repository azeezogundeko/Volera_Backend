from asyncio import gather, to_thread

import asyncio
from typing import Dict, List, Optional

from datetime import datetime
from .services import (
    get_user_growth_data, 
    get_daily_users_data, 
    get_error_rate_data, 
    get_date_logs,
    calculate_error_rate,
    generate_email_html,
    get_all_users
    )

from .email_templates import EMAIL_TEMPLATES, BASE_TEMPLATE, get_email_template_by_id
from .model import Contact, EmailConfig, AdminUsers, AppLog, WaitList
from .email_manager import EmailManager
from .schema import AdminUserIn, EmailTemplatePreview, EmailTemplateResponse, SendEmailRequest
from ..auth.services import get_user_by_email, authenticate_user, create_access_token, split_name
from db import user_db

from utils.decorator import admin_required, super_admin_required
from utils.logging import logger
from utils.limiter import Limiter

from appwrite import query
from fastapi import APIRouter, Body, HTTPException, Request, Query

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
        admin_password = "your_secure_password"  # Provide a valid password or remove if not needed
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


# @admin_required
@router.get("/email/templates", response_model=List[EmailTemplateResponse])
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
        html = generate_email_html(content)
        
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

@admin_required
@router.get("/users")
async def get_all_user(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    """
    Get all users with pagination support.
    - limit: Number of users per page (1-100)
    - offset: Number of users to skip
    - search: Optional search term for email or name
    - status: Optional filter by user status
    """
    try:
        queries = []
        
        # Add search filter if provided
        if search:
            queries.extend([
                query.search("email", search),
                query.search("name", search)
            ])
            
        # Add status filter if provided
        if status:
            queries.append(query.equal("status", status))
            
        # Get total count for pagination
        total_users = await user_db.count(queries)
        
        # Get paginated users
        users = await user_db.list(
            queries=queries,
            limit=limit,
            offset=offset
        )
        
        return {
            "users": users,
            "total": total_users,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}", exc_info=True)
        raise HTTPException(500, "Failed to fetch users")

@admin_required
@router.get("/users/label/{label}")
async def get_users_by_label(
    label: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get users by label with pagination support.
    - label: The label to filter users by (e.g., 'premium', 'active', 'inactive')
    - limit: Number of users per page (1-100)
    - offset: Number of users to skip
    """
    try:
        # Create query for label filter
        queries = [query.equal("label", label)]
        
        # Get total count for pagination
        total_users = await user_db.count(queries)
        
        # Get paginated users with the specified label
        response = await user_db.list(
            queries=queries,
            limit=limit,
            offset=offset
        )
        
        if not response:
            return {
                "users": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
            
        return {
            "users": response["users"] if "users" in response else response,
            "total": total_users,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error fetching users by label: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to fetch users with label '{label}'")

users_emails = [
    "volera.engr@gmail.com",
    "azeez@volaera.app",
    "volera.engr@gmail.com",
    "volera.engr@gmail.com",
    "volera.engr@gmail.com",
    "volera.engr@gmail.com",
    "volera.engr@gmail.com",
    "volera.engr@gmail.com",
]

users_names = [
    "Volera Engr",
    "Azeez",
    "Volera Engr",
    "Volera Engr",
    "Volera Engr",
    "Volera Engr",
    "Volera Engr",
    "Volera Engr",
]

# @admin_required
@router.post("/email/bulk/send")
async def send_users_email(
    request: Request,
    email_request: SendEmailRequest
):
    # print(email_request)
    try:
        batch_size = 50  # Process users in batches of 50
        offset = 0
        all_users = []
        template = get_email_template_by_id(str(email_request.template_id))
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template not found"
            )
        html_content = generate_email_html(email_request, template)

        # Get users based on selection criteria
        if email_request.emails:
            # Get specific users
            for email in email_request.emails:
                user = await get_user_by_email(email)
                if user is None:
                    continue   
                all_users.append(user.__dict__)

            if not all_users:
                raise HTTPException(
                    status_code=400,
                    detail="No users found matching the criteria"
                )

            result = email_manager.send_bulk_email(
                subject=email_request.subject,
                content=html_content,
                emails=[user["email"] for user in all_users],
                account_key=email_request.account_key,
                usernames=[split_name(user["name"])[0] for user in all_users]
            )
        
            return {
                "success": True,
                "message": f"Email sending queued for {len(all_users)} recipients",
                "data": {
                    "task_id": result["task_id"],
                    "recipients_count": len(all_users)
                }
            }
        emails_set = set()
        usernames_set = set()

        # Use the label query for filtering
        queries = []

        if email_request.filters == 'waitlist':
            
            while True:
                queries.append(query.Query.limit(batch_size))
                queries.append(query.Query.offset(offset))
                waitlist = await WaitList.list(queries)

                if waitlist["total"] == 0:
                    break

                if len(waitlist["documents"]) < batch_size:  # Last batch
                    break

                documents = waitlist["documents"]
                for doc in documents:
                    emails_set.add(doc.email)
                    usernames_set.add(doc.email.split("@")[0])

            print(emails_set)
            print(usernames_set)

        elif email_request.filters == 'all':
            # Fetch users in batches
            while True:
                queries.append(query.Query.limit(batch_size))
                queries.append(query.Query.offset(offset))
                batch = await get_all_users(queries)
                users_batch = batch["users"]
                
                if not users_batch:
                    break
                    
                all_users.extend(users_batch)
                offset += batch_size

                if len(users_batch) < batch_size:  # Last batch
                    break

            for user in all_users:
                emails_set.add(user["email"])
                usernames_set.add(split_name(user["name"])[0])

        else:
            if email_request.filters == "active":
                filters = ["subscribed"]
            elif email_request.filters == "inactive":
                filters = ["unsubscribed"]
                
            queries.append(query.equal("label", filters))

            # Fetch users in batches
            while True:
                queries.append(query.Query.limit(batch_size))
                queries.append(query.Query.offset(offset))
                batch = await get_all_users(queries)
                users_batch = batch["users"]
                
                if not users_batch:
                    break
                    
                all_users.extend(users_batch)
                offset += batch_size
                
                if len(users_batch) < batch_size:  # Last batch
                    break

            # Use the label query for filtering
            for user in all_users:
                emails_set.add(user["email"])
                usernames_set.add(split_name(user["name"])[0])
        
        usernames = list(usernames_set)
        emails = list(emails_set)

 

        if not usernames:
            raise HTTPException(
                status_code=400,
                detail="No users found matching the criteria"
            )
       
        # Extract emails and usernames from all_users
        
        result = email_manager.send_bulk_email(
            subject=email_request.subject,
            content=html_content,
            emails=emails,
            usernames=usernames,
            account_key=email_request.account_key
        )

        return {
            "success": True,
            "message": f"Email sending queued for {len(all_users)} recipients",
            "data": {
                "task_id": result["task_id"],
                "recipients_count": len(all_users)
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

@super_admin_required
@router.post("/clear-cache")
async def clear_all_caches():
    """
    Clear both VectorStore and DiskCacheDB caches.
    This endpoint requires super admin privileges.
    """
    try:
        # Initialize both caches
        from db.cache.dict import VectorStore, DiskCacheDB
        
        vector_store = VectorStore()
        disk_cache = DiskCacheDB()
        
        # Initialize both caches
        await vector_store.initialize()
        await disk_cache.initialize()
        
        # Clear VectorStore by deleting all keys
        if vector_store.use_qdrant and vector_store.qdrant_client:
            # Delete the entire collection for Qdrant
            await asyncio.to_thread(
                vector_store.qdrant_client.delete_collection,
                collection_name=vector_store.collection_name
            )
            # Reinitialize to create a fresh collection
            await vector_store._init_qdrant()
        else:
            # For FAISS, reinitialize the index
            await vector_store._init_faiss()
        
        # Clear DiskCache
        await disk_cache.clear()
        
        logger.info("Successfully cleared both VectorStore and DiskCacheDB caches")
        return {"message": "Successfully cleared all caches"}
        
    except Exception as e:
        logger.error(f"Error clearing caches: {str(e)}", exc_info=True)
        raise HTTPException(500, f"Failed to clear caches: {str(e)}")
