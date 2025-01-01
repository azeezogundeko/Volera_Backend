from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
import uuid

# Core User Class
@dataclass
class User:
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier
    email: str
    password_hash: str  # Store securely hashed passwords

# Profile Class for User's Personal Information
@dataclass
class UserProfile:
    full_name: str
    profile_picture_url: Optional[str] = None
    date_registered: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

# Preferences Class for Shopping Preferences
@dataclass
class ShoppingPreferences:
    favorite_categories: List[str] = field(default_factory=list)
    saved_searches: List[str] = field(default_factory=list)
    wishlist: List[Dict[str, str]] = field(default_factory=list)  # Example: {"item_name": "Laptop", "url": "example.com"}
    preferred_brands: List[str] = field(default_factory=list)
    price_range: Optional[Dict[str, float]] = field(default_factory=lambda: {"min": 0.0, "max": 0.0})

# Activity Data Class
@dataclass
class UserActivity:
    search_history: List[Dict[str, str]] = field(default_factory=list)  # Example: {"query": "laptop", "timestamp": "2024-12-31"}
    click_behavior: List[Dict[str, str]] = field(default_factory=list)  # Example: {"item_id": "123", "timestamp": "2024-12-31"}
    interaction_data: List[Dict[str, str]] = field(default_factory=list)  # Example: {"action": "liked", "item_id": "123"}

# Communication and Notification Preferences
@dataclass
class CommunicationPreferences:
    notification_preferences: Dict[str, bool] = field(default_factory=lambda: {
        "email": True,
        "push": True,
        "sms": False
    })
    referral_code: Optional[str] = None

# Metadata Class for Technical Details
@dataclass
class TechnicalMetadata:
    device_info: Optional[Dict[str, str]] = field(default_factory=dict)  # Example: {"device": "iPhone", "os": "iOS"}
    ip_address: Optional[str] = None
    session_tokens: List[str] = field(default_factory=list)

# Purchase History and Feedback
@dataclass
class AdvancedInsights:
    purchase_history: List[Dict[str, str]] = field(default_factory=list)  # Example: {"item_name": "Laptop", "date": "2024-12-30"}
    feedback: List[Dict[str, str]] = field(default_factory=list)  # Example: {"feedback": "Great app!", "rating": "5"}

# Security and Compliance
@dataclass
class SecurityCompliance:
    two_factor_auth: bool = False
    consent_to_terms: bool = False

# Example of Composing a User with Additional Classes
@dataclass
class CompleteUser:
    user: User
    profile: UserProfile
    preferences: ShoppingPreferences
    activity: UserActivity
    communication: CommunicationPreferences
    technical_metadata: TechnicalMetadata
    insights: AdvancedInsights
    security: SecurityCompliance

# Example Usage
user = User(email="johndoe@example.com", password_hash="hashedpassword123")
profile = UserProfile(full_name="John Doe")
preferences = ShoppingPreferences(favorite_categories=["electronics", "fashion"])
activity = UserActivity()
communication = CommunicationPreferences()
technical_metadata = TechnicalMetadata()
insights = AdvancedInsights()
security = SecurityCompliance(consent_to_terms=True)

complete_user = CompleteUser(
    user=user,
    profile=profile,
    preferences=preferences,
    activity=activity,
    communication=communication,
    technical_metadata=technical_metadata,
    insights=insights,
    security=security
)

print(complete_user)
