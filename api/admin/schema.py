from pydantic import BaseModel
from typing import Optional, List, Dict, Literal

class AdminUserIn(BaseModel):
    email: str
    editor: bool = False
    email_key: str
    super_admin: bool = False

class EmailTemplateResponse(BaseModel):
    """Response model for email templates matching TypeScript interface"""
    id: str
    name: str
    subject: str
    content: str
    description: str
    last_used: Optional[str] = None
    variables: List[str]
    html_preview: Optional[str] = None

class EmailTemplatePreview(BaseModel):
    """Request model for email template preview"""
    content: str
    variables: Dict[str, str]

class SendEmailRequest(BaseModel):
    """Request model for sending emails to users"""
    template_id: Optional[str] = None
    subject: str
    content: str
    account_key: str
    emails: Optional[List[str]] = None  
    variables: Optional[Dict[str, str]] = None 
    filters: Literal["active", "inactive", "waitlist", "all"] = None