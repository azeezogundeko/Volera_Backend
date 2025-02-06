from db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField


# class AdminUser

class Contact(AppwriteModelBase):
    collection_id = "contact"

    email: str = AppwriteField()
    name: str = AppwriteField()
    message: str = AppwriteField(type="string", size=43_000)