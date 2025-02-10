from pydantic import BaseModel

class AdminUserIn(BaseModel):
    email: str
    editor: bool = False
    email_key: str
    super_admin: bool = False
