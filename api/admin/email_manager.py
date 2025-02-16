from typing import List, Dict, Optional
from utils.celery_tasks import send_bulk_email
from utils.logging import logger
from .model import EmailConfig, EmailTemplate

class EmailManager:
    """Manages email operations for admin functionality"""
    
    def __init__(self):
        """Initialize the EmailManager"""
        pass

    async def get_config(self) -> Dict:
        """Get the current email configuration"""
        try:
            config = await EmailConfig.get_current_config()
            if not config:
                raise ValueError("Email configuration not found")
            return config
        except Exception as e:
            logger.error(f"Error getting email config: {str(e)}")
            raise

    async def send_bulk_email(self, subject: str, content: str, recipient_filter: str) -> Dict:
        """
        Send bulk email to filtered recipients
        
        Args:
            subject: Email subject
            content: Email content (HTML)
            recipient_filter: Filter criteria for recipients
            
        Returns:
            Dict with status and task information
        """
        try:
            # Get email configuration
            config = await self.get_config()
            
            # Get recipient list based on filter
            recipients = await self._get_recipients(recipient_filter)
            
            if not recipients:
                raise ValueError("No recipients found matching the filter criteria")

            # Send bulk email using Celery task
            result = send_bulk_email.delay(
                emails=recipients,
                subject=subject,
                html_content=content,
                from_name=config.get('from_name'),
                account_key=config.get('account_key', 'support'),
                priority='normal'
            )

            return {
                "success": True,
                "message": f"Bulk email task initiated for {len(recipients)} recipients",
                "task_id": str(result.id)
            }

        except Exception as e:
            logger.error(f"Error sending bulk email: {str(e)}")
            raise

    async def _get_recipients(self, filter_criteria: str) -> List[str]:
        """
        Get list of recipient emails based on filter criteria
        
        Args:
            filter_criteria: Criteria to filter recipients
            
        Returns:
            List of email addresses
        """
        # TODO: Implement recipient filtering logic based on your user model
        # This is a placeholder that should be implemented based on your needs
        return []

    async def get_templates(self) -> List[Dict]:
        """Get available email templates"""
        try:
            return EmailTemplate.get_default_templates()
        except Exception as e:
            logger.error(f"Error getting email templates: {str(e)}")
            raise
