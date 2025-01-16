import asyncio

from appwrite.client import AppwriteException
from fastapi.background import BackgroundTasks
from . import services
from .schema import User, UserIn, UserPublic, UserOut, UserProfileOut
from .schema_in import UserCreate, LoginSchema, ProfileSchema
from db import user_db
from .model import UserProfile
from appwrite.input_file import InputFile
from appwrite import query



from fastapi import Depends, HTTPException, APIRouter, UploadFile, File
# from fastapi.responses import JSONResponse


router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register_user(payload: UserCreate, background_tasks: BackgroundTasks):
    return await services.create_new_user(payload, background_tasks)


@router.post("/verify_account")
async def verify_account(
    verification_code: int,
    user: UserIn = Depends(services.get_current_user),
):

    valid_code = user.prefs["validation_code"]

    if verification_code == valid_code:
        await asyncio.to_thread(user_db.update_status, user.id, True)
        await asyncio.to_thread(user_db.update_email_verification, user.id, True)
        return {"message": "success"}
    else:
        raise HTTPException(status_code=400, detail="Invalid verification code")


@router.get("/resend-verification-code")
async def resend_verification_code(
    background_tasks: BackgroundTasks,
    user: UserIn = Depends(services.get_current_user),
):
    
    background_tasks.add_task(services.send_new_user_email, user.prefs["vaidation_code"], user.email)
    return {"message": "success"}
    

@router.post("/login", response_model=UserPublic)
async def login(payload: LoginSchema):
    user = await services.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = services.create_access_token(data={"sub": payload.email})
    first_name, last_name = user.name.rsplit("_", 1)
    is_pro = True if "pro_user" in user.labels else False
   

    profile = await UserProfile.list(queries=[query.Query.equal("user_id", user.id)])
    image_id = profile.avatar
    image_data = None
    if image_id:
        try:
            image_data = await UserProfile.get_file(image_id)
        except AppwriteException:
            pass

    user = UserOut(
        user_id=user.id,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_pro=is_pro,
        profile_image=image_data,
    )
    return  {
        "user": user,
        "token": {"access_token": access_token, "token_type": "bearer"}
        }

@router.post("/onboarding", response_model=UserProfileOut)
async def create_user_profile(
    profile: ProfileSchema = Depends(),
    user: UserIn = Depends(services.get_current_user)
):
    result = await services.create_user_profile(user, profile)
    return {
        "message": "success",
        "data": result,
        "error": None
    }

@router.post("/notifications")
async def set_notifications(
    notifications: bool,
    user: UserIn = Depends(services.get_current_user)):
        
    return await asyncio.to_thread(user_db.update_prefs, user.id, {"notification": notifications})


@router.post("/profile-picture")
async def update_profile_image(
    profilePicture: UploadFile = File(...),
    user: UserIn = Depends(services.get_current_user)):
    
    file = InputFile.from_bytes(
        profilePicture.file.read(),
        profilePicture.filename
    )
    profile = UserProfile.list([query.Query.equal("user_id", user.id)], limit=1)
    await UserProfile.update_file(profile["documents"][0].id, file)
     


@router.get("/me", response_model=User)
async def get_me(current_user: UserIn = Depends(services.get_current_user)):
    return current_user