from fastapi import APIRouter, Body

from .model import Contact

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
