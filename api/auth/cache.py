from typing import Optional
import random

from config import EMAIL_CACHE_DIR  # Make sure to set this in your config
from utils.logging import logger
from diskcache import Cache

class EmailValidationManager:
    def __init__(self):
        # Initialize the cache directory for email validations.
        self.cache = Cache(directory=str(EMAIL_CACHE_DIR))
        # Set TTL to 15 minutes (15*60 seconds)
        self.ttl = 15 * 60

    def generate_code(self, email: str) -> str:
        """
        Generate a 6-digit validation code for the provided email address and store it
        in the cache with a TTL of 15 minutes.
        """
        try:
            # Generate a 6-digit code
            code = str(random.randint(100000, 999999))
            # Normalize the email to avoid case and whitespace issues
            email_key = email.lower().strip()
            # Store the code with the TTL
            self.cache.set(email_key, code, expire=self.ttl)
            return code
        except Exception as e:
            logger.error(f"Failed to generate code for {email}: {str(e)}")
            raise

    def validate_code(self, email: str, code: str) -> bool:
        """
        Validate the provided code against the stored code for the email.
        If valid, optionally remove the stored code.
        """
        try:
            email_key = email.lower().strip()
            stored_code = self.cache.get(email_key)
            if stored_code == code:
                # Optionally, delete the code after successful validation to prevent reuse
                self.cache.delete(email_key)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to validate code for {email}: {str(e)}")
            return False

# Create a singleton instance
email_validation_manager = EmailValidationManager()
