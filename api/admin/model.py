from __future__ import annotations

from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from typing import Dict, Optional, List
import uuid
from enum import Enum
from datetime import datetime

from appwrite.client import AppwriteException


class Contact(AppwriteModelBase):
    collection_id = "contact"

    email: str = AppwriteField()
    name: str = AppwriteField()
    message: str = AppwriteField(type="string", size=43_000)
    acknowledged: bool = AppwriteField(type="bool", default=False)

class WaitList(AppwriteModelBase):
    collection_id= "waitlist"
    email: str = AppwriteField()
    
class AdminUsers(AppwriteModelBase):
    collection_id = "admin_users"

    is_super_admin: bool = AppwriteField(type="bool", default=False)
    admin_email: str = AppwriteField(required=False)
    email_key: str = AppwriteField(required=False)
    # admin_password: str = AppwriteField()
    is_editor: str = AppwriteField(type="bool", default=False)


class AppLog(AppwriteModelBase):
    collection_id = "app_log"

    id: str = AppwriteField()
    no_of_users: int = AppwriteField(type="int", default=0)
    total_revenue_generated: float = AppwriteField(type="float", default=0.0)
    no_of_transactions: int = AppwriteField(type="int", default=0)
    # total_active_users: int = AppwriteField(default=0, type="int")
    # total_inactive_users: int = AppwriteField(default=0, type="int")

    @classmethod
    async def get_or_create(cls, document_id: str) -> "AppLog":
        """Get an existing log or create a new one with default values."""
        try:
            return await cls.read(document_id)
        except AppwriteException:
            return await cls.create(document_id, {
                "id": document_id,
                "no_of_users": 0,
                "total_revenue_generated": 0.0,
                "no_of_transactions": 0
            })


    @classmethod
    async def update_log(cls, type: "user" | "transaction", amount: float = None) -> None:
        """
        Update daily usage for a given user at the provided timestamp.
        """
        document_id = "engr_ogundeko_volera"
        dict_to_update = {}  # Initialize dict_to_update at the start

        if type in ["user", "transaction"]:
            try:
                doc = await cls.read(document_id)
                if type == "user":
                    dict_to_update["no_of_users"] = doc.no_of_users + 1
                elif type == "transaction": 
                    dict_to_update["total_revenue_generated"] = doc.total_revenue_generated + (amount or 0)
                    dict_to_update["no_of_transactions"] = doc.no_of_transactions + 1

                await cls.update(document_id, dict_to_update)

            except AppwriteException:
                # Set default values for new document
                dict_to_update = {
                    "id": document_id,  # Required by Appwrite
                    "no_of_users": 1 if type == "user" else 0,
                    "total_revenue_generated": amount if type == "transaction" else 0.0,
                    "no_of_transactions": 1 if type == "transaction" else 0
                }
                await cls.create(document_id, dict_to_update)

        
    
class DailyLog(AppwriteModelBase):
    collection_id = "user_daily_log"

    day: str = AppwriteField() # store as YYYY-MM-DD string
    no_of_transactions: int = AppwriteField(type="int", default=0)
    no_of_errors: int = AppwriteField(type="int", default=0)
    total_users: int = AppwriteField(default=0, type="int")
    total_revenue_generated: int = AppwriteField(type="float", default=0.0)


    total_active_users: int = AppwriteField(default=0, type="int")
    total_inactive_users: int = AppwriteField(default=0, type="int")


    @classmethod
    async def get_or_create(cls, document_id: str) -> Optional[DailyLog]:
        return await super().get_or_create(document_id, {"day": document_id}) 

          
    @classmethod
    async def update_log(cls, type: "user" | "error" | "transaction", amount: float = None) -> None:
        """
        Update daily usage for a given user at the provided timestamp.
        """
        document_id = datetime.now().strftime("%Y-%m-%d")
        dict_to_update = {}

        try:
            daily_doc: DailyLog = await cls.read(document_id)

            if type == "user":
                dict_to_update["total_users"] = daily_doc.total_users + 1
            elif type == "error":
                dict_to_update["no_of_errors"] = daily_doc.no_of_errors + 1
            elif type == "transaction":
                dict_to_update["no_of_transactions"] = daily_doc.no_of_transactions + 1
                dict_to_update["total_revenue_generated"] = daily_doc.total_revenue_generated + (amount or 0)

            await cls.update(document_id, dict_to_update)

        except AppwriteException:
            # Document does not exist; create a new one with proper defaults
            dict_to_update = {
                "day": document_id,
                "total_users": 1 if type == "user" else 0,
                "no_of_errors": 1 if type == "error" else 0,
                "no_of_transactions": 1 if type == "transaction" else 0,
                "total_revenue_generated": amount if type == "transaction" else 0,
                "total_active_users": 0,
                "total_inactive_users": 0
            }
            await cls.create(document_id, dict_to_update)


class MonthlyLog(AppwriteModelBase):
    collection_id = "user_monthly_log"

    month: str = AppwriteField() # store as YYYY-MM string
    total_users: int = AppwriteField(default=0, type="int")
    total_active_users: int = AppwriteField(default=0, type="int")
    no_of_errors: int = AppwriteField(default=0, type="int")
    total_revenue_generated: int = AppwriteField(type="float", default=0.0)

    total_inactive_users: int = AppwriteField(default=0, type="int")
    no_of_transactions: int = AppwriteField(type="int", default=0)


    @classmethod
    async def get_or_create(cls, document_id: str) -> MonthlyLog:
        return await super().get_or_create(document_id, {"month": document_id})

    @classmethod
    async def update_log(cls, type: "user" | "error" | "transaction", amount: float = None) -> None:
        """
        Update monthly usage for a given user at the provided timestamp.
        """
        document_id = datetime.now().strftime("%Y-%m")
        dict_to_update = {}

        try:
            monthly_doc: MonthlyLog = await cls.read(document_id)
            if type == "user":
                dict_to_update["total_users"] = monthly_doc.total_users + 1
            elif type == "error":
                dict_to_update["no_of_errors"] = monthly_doc.no_of_errors + 1
            elif type == "transaction":
                dict_to_update["no_of_transactions"] = monthly_doc.no_of_transactions + 1
                dict_to_update["total_revenue_generated"] = monthly_doc.total_revenue_generated + (amount or 0)

            await cls.update(document_id, dict_to_update)

        except AppwriteException:
            # Document does not exist; create a new one with proper defaults
            dict_to_update = {
                "month": document_id,
                "total_users": 1 if type == "user" else 0,
                "no_of_errors": 1 if type == "error" else 0,
                "no_of_transactions": 1 if type == "transaction" else 0,
                "total_revenue_generated": amount if type == "transaction" else 0,
                "total_active_users": 0,
                "total_inactive_users": 0
            }
            await cls.create(document_id, dict_to_update)



class BaseModel:
    @staticmethod
    def get_unique_id():
        return str(uuid.uuid4())
    
    @classmethod
    async def create(cls, id: str, data: Dict):
        # Implementation depends on your database
        pass
    
    @classmethod
    async def get(cls, id: str):
        # Implementation depends on your database
        pass

class EmailConfig(BaseModel):
    """Stores email configuration for the admin"""
    @classmethod
    async def get_current_config(cls) -> Optional[Dict]:
        # This would typically fetch from your database
        # For now, returning a mock configuration
        return {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_user": "your-email@gmail.com",
            "smtp_password": "your-app-password",
            "from_email": "your-email@gmail.com",
            "from_name": "Your Name"
        }

class TemplateType(Enum):
    WELCOME = "welcome"
    NEW_FEATURE = "new_feature"
    PRICE_DROP = "price_drop"
    POLICY_CHANGE = "policy_change"
    NEWSLETTER = "newsletter"

class EmailTemplate(BaseModel):
    """Stores email templates"""
    collection_id = "email_templates"

    name: str = AppwriteField()
    subject: str = AppwriteField()
    content: str = AppwriteField(type="string", size=43_000)
    template_type: str = AppwriteField()
    created_at: datetime = AppwriteField()
    updated_at: datetime = AppwriteField()

    @classmethod
    def get_default_templates(cls) -> List[Dict]:
        return [
            {
                "id": "welcome_template",
                "name": "Welcome Email",
                "subject": "Welcome to Volera!",
                "template_type": TemplateType.WELCOME.value,
                "content": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #50C878; margin-bottom: 20px;">Welcome to Volera!</h2>
                    <p>Dear {{name}},</p>
                    <p>We're thrilled to welcome you to Volera! Thank you for joining our community of innovative minds.</p>
                    <p>Here's what you can expect from us:</p>
                    <ul style="list-style-type: none; padding-left: 0;">
                        <li style="margin: 10px 0;">🚀 Cutting-edge features and updates</li>
                        <li style="margin: 10px 0;">💡 Exclusive insights and tips</li>
                        <li style="margin: 10px 0;">🤝 Dedicated support whenever you need it</li>
                    </ul>
                    <p>Get started by exploring our platform, and don't hesitate to reach out if you have any questions!</p>
                    <div style="margin: 30px 0;">
                        <a href="[Dashboard URL]" style="background-color: #50C878; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a>
                    </div>
                    <p>Best regards,<br>The Volera Team</p>
                </div>
                """
            },
            {
                "id": "new_feature_template",
                "name": "New Feature Announcement",
                "subject": "Exciting New Features Just Launched! 🚀",
                "template_type": TemplateType.NEW_FEATURE.value,
                "content": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #50C878; margin-bottom: 20px;">New Features Are Here!</h2>
                    <p>Hi {{name}},</p>
                    <p>We're excited to announce some powerful new features that just landed on Volera!</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #50C878;">What's New:</h3>
                        <ul>
                            {{features_list}}
                        </ul>
                    </div>
                    <p>Ready to try these new features?</p>
                    <div style="margin: 30px 0;">
                        <a href="[Features URL]" style="background-color: #50C878; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Explore New Features</a>
                    </div>
                    <p>We'd love to hear your feedback!</p>
                </div>
                """
            },
            {
                "id": "price_drop_template",
                "name": "Price Drop Alert",
                "subject": "Price Drop Alert: Items in Your Wishlist! 💰",
                "template_type": TemplateType.PRICE_DROP.value,
                "content": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #50C878; margin-bottom: 20px;">Price Drop Alert!</h2>
                    <p>Hello {{name}},</p>
                    <p>Great news! Some items in your wishlist have dropped in price:</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        {{price_drop_items}}
                    </div>
                    <p>Don't miss out on these savings!</p>
                    <div style="margin: 30px 0;">
                        <a href="[Wishlist URL]" style="background-color: #50C878; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View Your Wishlist</a>
                    </div>
                </div>
                """
            },
            {
                "id": "policy_change_template",
                "name": "Policy Update Notice",
                "subject": "Important: Updates to Our Policies",
                "template_type": TemplateType.POLICY_CHANGE.value,
                "content": """
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #50C878; margin-bottom: 20px;">Policy Updates</h2>
                    <p>Dear {{name}},</p>
                    <p>We're writing to inform you about important updates to our policies, effective {{effective_date}}.</p>
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #50C878;">Key Changes:</h3>
                        {{policy_changes}}
                    </div>
                    <p>For a detailed overview of these changes, please visit our updated policy page:</p>
                    <div style="margin: 30px 0;">
                        <a href="[Policy URL]" style="background-color: #50C878; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">View Full Policy</a>
                    </div>
                    <p>If you have any questions about these changes, please don't hesitate to contact our support team.</p>
                </div>
                """
            }
        ]

    def html_footer(self):
        privacy_link = "[Privacy Policy URL]"  # Replace with actual URL
        return f"""<div style="text-align: center; color: #333333; font-size: 12px; background-color: #ffffff; padding: 20px; border-top: 1px solid #e0e0e0;">
            <p style="margin: 0;">Follow our journey:<br>
            <a href="[LinkedIn Placeholder]" style="color: #50C878; text-decoration: underline;">LinkedIn</a> |
            <a href="[X Placeholder]" style="color: #50C878; text-decoration: underline;">X</a> |
            <a href="[Bluesky Placeholder]" style="color: #50C878; text-decoration: underline;">Bluesky</a> |
            <a href="[WhatsApp Community Placeholder]" style="color: #50C878; text-decoration: underline;">Join our WhatsApp Community</a>
            </p>
            <p style="margin: 5px 0;">© 2024 Volera. All rights reserved.</p>
            <p style="margin: 5px 0;">
                <a href="{privacy_link}" style="color: #50C878; text-decoration: underline;">Privacy Policy</a>
            </p>
        </div>"""

    def compose_email(self, subject: str, content: str, recipient: str):
        return f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f4f4f4;">
            <div style="width: 100%; max-width: 600px; margin: 0 auto; background-color: white;">
                {content}
                {self.html_footer()}
            </div>
        </body>
        </html>
        """

class User(BaseModel):
    """User model for managing recipients"""
    @classmethod
    async def get_filtered_users(cls, filter_type: str) -> list[Dict]:
        # Implementation depends on your database
        # This would fetch users based on the filter
        pass