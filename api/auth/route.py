import asyncio
import base64

from db import user_db
from . import services
from .model import UserPreferences, UserProfile
from .email import send_forgot_password_email
from .schema import UserIn, UserPublic, UserPreferenceSchemaOut
from .schema_in import UserCreate, LoginSchema, ProfileSchema, Profile
from config import APPWRITE_BUCKET_ID, APPWRITE_ENDPOINT

from utils.decorator import auth_required
from utils.logging import logger

# from appwrite import query
from fastapi import Request
from appwrite.client import AppwriteException
from fastapi.background import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi import Depends, HTTPException, APIRouter, UploadFile, File, Body



router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register_user(payload: UserCreate, background_tasks: BackgroundTasks):
    return await services.create_new_user(payload, background_tasks)



@router.post("/verify_account")
async def verify_account(
    email: str = Body(),
    code: int =  Body()):

    user = await services.get_user_by_email(email)
    if user is None:
        raise HTTPException(400, "User not found")

    valid_code = user.prefs["validation_code"]

    if code == valid_code:
        await asyncio.to_thread(user_db.update_status, user.id, True)
        await asyncio.to_thread(user_db.update_email_verification, user.id, True)
        return {"message": "success"}
    raise HTTPException(status_code=400, detail="Invalid verification code")


@router.post("/forgot_password")
async def forgot_password(background_tasks: BackgroundTasks, email: str = Body()):
    user = await services.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=400, detail="Email does not exist")

    code = services.generate_random_six_digit_number()
    user_db.update_prefs(user.id, {"code": code})
    first_name, last_name = services.split_name(user.name)
    # send user email for otp
    background_tasks.add_task(send_forgot_password_email, email, first_name, code)

    return {"message": "success"}

    
@router.post("/verify_code")
async def verify_password_code(code: int = Body(), email: str= Body()):
    user = await services.get_user_by_email(email)

    if user is None:
        raise HTTPException(status_code=400, detail="User not found")

    password_code = user.prefs.get("code")

    if password_code != code:
        raise HTTPException(400, "Code is invalid")


    return {'message': 'success'}


@router.post("/reset_password")
async def change_forgot_password(email: str = Body(), code: int = Body(),  password: str = Body()):


    user = await services.get_user_by_email(email)
    if user is None:
        raise HTTPException(400, "User was not found")
    v_code = user.prefs.get("code")

    if v_code != code:
        raise HTTPException(status_code=400, detail="Verification code is invalid")

    password = services.get_password_hash(password)
    await asyncio.to_thread(user_db.update_password, user.id, password)
    return {"message": "success"}

    
@auth_required
@router.put("/change_password")
async def change_user_password(request: Request, currentPassword: str = Body(), newPassword: str = Body()):
    user = request.state.user

    old_hash_password = services.get_password_hash(currentPassword)
    is_valid = services.verify_password(currentPassword, old_hash_password)

    if not is_valid:
        raise HTTPException(400, "User password is Invalid")

    new_hash_password = services.get_password_hash(newPassword)
    await asyncio.to_thread(user_db.update_password, user.id, new_hash_password)

    return {"message": "Password changes successfully"}


@router.post("/resend-verification-code")
async def resend_verification_code(
    background_tasks: BackgroundTasks,
    email: str = Body(),
    ):
    # user = request.state.user
    user = await services.get_user_by_email(email)
    if user is None:
        raise HTTPException(400, "Account was not found")
    background_tasks.add_task(services.send_new_user_email, user.prefs["validation_code"], email)
    return {"message": "success"}
    


@router.post("/login", response_model=UserPublic)
async def login(payload: LoginSchema):
    user = await services.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = services.create_access_token(data={"sub": payload.email})
    first_name, last_name = user.name.rsplit("_", 1)
    is_pro = True if "subscribed" in user.labels else False
    image_data = None
   
    try:
        profile = await UserProfile.read(user.id)
        image_id = profile.avatar
        if image_id:
            try:
                raw_image_data = await UserProfile.get_file(image_id)
                image_data = base64.b64encode(raw_image_data).decode("utf-8")
            except AppwriteException:
                pass

    except AppwriteException:
        pass

    user = dict(
        id=user.id,
        email=user.email,
        first_name=first_name,
        last_name=last_name,
        name= first_name + '_' + last_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        is_pro=is_pro,
        profile_image=image_data,
    )
    return  {
        "user": user,
        "token": {"access_token": access_token, "token_type": "bearer"}
        }

@auth_required
@router.post("/onboarding")
async def create_user_profile(
    request: Request,
    profile: ProfileSchema = Depends(),
):
    user: UserIn = request.state.user
    await services.create_user_profile(user, profile)
    return {"message": "success", "error": None}

@auth_required
@router.post("/notifications")
async def set_notifications(
    request: Request,
    notifications: bool ):
        
    user = request.state.user      
    return await asyncio.to_thread(user_db.update_prefs, user.id, {"notification": notifications})


@auth_required
@router.post("/profile/image")
async def update_profile_image(
    request: Request, 
    profilePicture: UploadFile = File()
):
    user: UserIn = request.state.user
    
    # Upload profile image and get file ID
    file_id = await UserProfile.upload_profile_image(user.id, profilePicture)
    
    return {
        "message": "Profile image uploaded successfully",
        "file_id": file_id
    }


@auth_required
@router.get("/profile")
async def get_profile(request: Request): 
    user: UserIn = request.state.user 
    try:
        profile = await UserProfile.read(user.id)
    except AppwriteException:
        raise HTTPException(400, "User has not created a profile")
    
    first_name, last_name = services.split_name(user.name)
    avatar = None
    if profile.avatar is not None:
        try:
            # Get file metadata instead of binary data
            file_metadata = await UserProfile.get_file_metadata(profile.avatar)
            avatar = {
                "id": profile.avatar,
                "name": file_metadata.get('name', 'avatar'),
                "url": f"{APPWRITE_ENDPOINT}/storage/buckets/{APPWRITE_BUCKET_ID}/files/{profile.avatar}/view"
            }
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error retrieving avatar metadata: {e}")
            avatar = None

    return {
        "first_name": first_name,
        "last_name": last_name,
        "gender": profile.gender,
        "email": user.email,
        "address": profile.address,
        "city": profile.city,
        "phone": profile.phone,
        "country": profile.country,
        "avatar": avatar,
    }


@auth_required
@router.put("/profile")
async def update_profile(request: Request, payload: Profile = Depends()): 
    user: UserIn = request.state.user
    # try:

    current_first_name, current_last_name = services.split_name(user.name)

    # Extract first and last name from payload, using current names as defaults
    first_name = payload.first_name or current_first_name
    last_name = payload.last_name or current_last_name

    # Construct the new full name
    new_name = f"{first_name}_{last_name}"

    # Prepare update payload
    update_data = {k: v for k, v in payload.__dict__.items() if v is not None}

    # Remove first_name and last_name from update_data as they're handled separately
    update_data.pop('first_name', None)
    update_data.pop('last_name', None)

    # Perform updates
    tasks = []

    # Handle avatar upload separately
    avatar = update_data.pop('avatar', None)
    email = update_data.pop('email', None)
    if avatar is not None:
        tasks.append(UserProfile.upload_profile_image(user.id, avatar))

    if email:
        if user.email != email:
            try:
                tasks.append(asyncio.to_thread(user_db.update_email, user.id, email))
            except AppwriteException:
                raise HTTPException(status_code=400, detail="Email has already been used")
    
    if new_name != user.name:
        # Update user's name in the user database
        tasks.append(asyncio.to_thread(user_db.update_name, user.id, new_name))

    if update_data:
        # Update user profile
        try:
            profile = await UserProfile.read(user.id)
            tasks.append(UserProfile.update(profile.id, update_data))
        except AppwriteException:
            tasks.append(UserProfile.create(user.id, update_data))

    if tasks:
        await asyncio.gather(*tasks)

    return {"message": "Profile updated successfully"}


@router.get('/preferences', response_model=UserPreferenceSchemaOut)
@auth_required
async def get_user_preference(request: Request):
    user = request.state.user
    try:
        return await UserPreferences.read(user.id)
    except AppwriteException:
        return {}


@router.put('/preferences')
@auth_required
async def update_preferences(request: Request, payload: UserPreferenceSchemaOut):
    user = request.state.user

    update_data = {k: v for k, v in payload.__dict__.items() if v is not None}
    try:
        try:
            await UserPreferences.update(user.id, update_data)
        except AppwriteException:
            await UserPreferences.create(user.id, update_data)

        return {"message": "User Preferences Updataed successfully"}
    except Exception as e:
        logger.error(f'Error {str(e)}', exc_info=True)
