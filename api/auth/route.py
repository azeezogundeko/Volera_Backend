import asyncio
import base64
from utils.request_session import http_client

from db import user_db
from . import services
from .model import UserPreferences, UserProfile, Referral
from .email import send_forgot_password_email, send_formal_welcome_email
from .schema import UserIn, UserPublic, UserPreferenceSchemaOut, ReferralSchemaOut
from .schema_in import UserCreate, LoginSchema, ProfileSchema, Profile
from config import (
    APPWRITE_BUCKET_ID, 
    APPWRITE_ENDPOINT, 
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET, 
    REDIRECT_URI
    )

from utils.decorator import auth_required
from utils.logging import logger

from appwrite import query
from fastapi import Request, Query
from appwrite.client import AppwriteException
from fastapi.background import BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi import Depends, HTTPException, APIRouter, UploadFile, File, Body

router = APIRouter()


@router.get("/referral", response_model=ReferralSchemaOut)
@auth_required
async def get_referral(request: Request, limit: int = Query(default=10)):
    user = request.state.user
    referred_users = []
    try:
        referral = await Referral.get_referral_by_user_id(user.id)
        if referral is None:
            # Create new referral and await it
            referral = await services.create_referral_code(user.id)

        # query_ = [query.Query.equal("referred_by", user.id)]
        # referred_users_ = await Referral.list(query_, limit=limit)
        # referred_users = []
        # if referred_users_["total"] > 0:
        #     user_ref_id = [user.user_id for user in referred_users_["documents"]]
        #     tasks = []
        #     for user_id in user_ref_id:
        #         tasks.append(services.get_user_by_id(user_id))
        #     users = await asyncio.gather(*tasks)
        #     referred_users = [{"id": user.id, "name": user.name, "email": user.email} for user in users]

        return {
            # "message": "Referral details retrieved successfully",
            # "error": None,
            "id": referral.id,
            "referral_code": referral.referral_code,
            "referral_count": referral.referral_count,
            "referral_limit": referral.referral_limit,
            "referred_users": referred_users,
            "referral_status": referral.referral_status
        }
    except Exception as e:
        logger.error(f'Error {str(e)}', exc_info=True)
        raise HTTPException(status_code=400, detail="Internal server error")


@router.get("/google/callback")
async def google_callback(request: Request, background_tasks: BackgroundTasks, code: str = Query()):
    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    # Prepare the token exchange request
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    # Exchange code for token
    token_resp = await http_client.post(token_url, data=data)
    token_json = token_resp.json()

    if token_resp.status_code != 200:
        raise HTTPException(status_code=token_resp.status_code, detail=token_json)

    access_token = token_json.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received")
    
    # Get user info from Google
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_response = await http_client.get(userinfo_url, headers=headers)
    userinfo = userinfo_response.json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="No email provided in user info")
    try:
        existing_user = await asyncio.to_thread(user_db.list, queries=[query.Query.equal('email', email)])
        existing_user = existing_user["users"][0]
    except Exception:
        existing_user = None

    print(existing_user)
    if existing_user is None:
        # For new users, create account
        given_name = userinfo.get("given_name", "")
        family_name = userinfo.get("family_name", given_name)
        user_response = await services.create_new_user(
            UserCreate(
                email=email,
                firstName=given_name,
                lastName=family_name,
                password=None, 
                auth_type="google"
            ),
            background_tasks
        )
        # Use the user data from the response
        user_data = user_response["user"]
        access_token = user_response["token"]["access_token"]
        return {
            "user": user_data,
            "token": {"access_token": access_token, "token_type": "bearer"}
        }
    else:
        # For existing users, format the response
        is_pro = True if "subscribed" in existing_user["labels"] else False
        first_name, last_name = existing_user["name"].rsplit("_", 1)
        access_token = services.create_access_token(data={"sub": existing_user["email"]})
        
        user_data = {
            "id": existing_user["$id"],
            "email": existing_user["email"],
            "first_name": first_name,
            "last_name": last_name,
            "name": f"{first_name}_{last_name}",
            "created_at": existing_user["$createdAt"],
            "updated_at": existing_user["$updatedAt"],
            "is_pro": is_pro,
            "profile_image": None,
            "is_new": False,
        }
        
        return {
            "user": user_data,
            "token": {"access_token": access_token, "token_type": "bearer"}
        }


@router.post("/register", response_model=UserPublic)
async def register_user(payload: UserCreate, background_tasks: BackgroundTasks):
    try:
        print(payload)
        return await services.create_new_user(payload, background_tasks)
    except Exception as e:
        print(e)
        logger.error(f'Error {str(e)}', exc_info=True)
        raise HTTPException(status_code=400, detail="Internal server error")


@router.post('/check-email')
async def check_email_availablity(email: str = Body()):
    user = await services.get_user_by_email(email)
    if user is None:
        return {"message": "success"}
    
    raise HTTPException(400, "Email already exists")

@router.post("/verify_account")
async def verify_account(
    background: BackgroundTasks,
    email: str = Body(),
    code: int =  Body(),
    ):

    user = await services.get_user_by_email(email)
    name = services.split_name(user.name)
    if user is None:
        raise HTTPException(400, "User not found")

    valid_code = user.prefs["validation_code"]

    if code == valid_code:
        await asyncio.to_thread(user_db.update_status, user.id, True)
        await asyncio.to_thread(user_db.update_email_verification, user.id, True)
        background.add_task(send_formal_welcome_email, email, name[0])
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
    


@router.post("/login")
async def login(request: Request, payload: LoginSchema):
    """
    User login endpoint with rate limiting protection.
    Rate limits:
    - 3 attempts per 30 minutes per email address
    """
    user = await services.authenticate_user(request, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    access_token = services.create_access_token(data={"sub": user.email})
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
