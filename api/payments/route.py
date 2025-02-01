import asyncio

from .model import Subscription
from .schema import PaymentData
from config import PAYSTACK_SECRET_KEY
from api.auth.services import get_user_by_email
from db import user_db

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body, status


# Load environment variables (ensure you have a .env file with PAYSTACK_SECRET_KEY set)
load_dotenv()

router = APIRouter()

class Plan:
    basic = {"price": 1000, "credits": 3000}
    premium = {"price": 3000, "credits": 7000}

    @classmethod
    def get_plan(cls, name) -> int:
        return getattr(cls, name, None)

    


@router.post("/initialize-payment")
async def initialize_payment(payment: PaymentData):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": payment.email,
        "amount": payment.amount,
        # Optionally, you can add a callback_url and metadata if needed
        # "callback_url": "https://yourdomain.com/payment-callback",
        # "metadata": {"custom_field": "value"}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        error_detail = response.json().get("message", "Payment initialization failed")
        raise HTTPException(status_code=500, detail=error_detail)

    response_data = response.json()

    # Return the access_code needed for the Paystack Popup on the frontend
    return {"access_code": response_data["data"]["access_code"]}


@router.post('/verify-payment')
async def verify_payment(
    reference: str = Body(),
    plan_name: str = Body(),
    email: str = Body(),
):
    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(404, detail='User was not found')

    url= f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
 
    if response.status_code != 200:
        raise HTTPException(404, detail="Reference code was not found")

    res = response.json()

    if res["status"] is True:
        data = res["data"]
        amount = data["amount"]
        currency = data["currency"]
        channel = data["channel"]

        pplan = Plan.get_plan(plan_name)

        if not pplan['price'] == amount:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=f"User paid incorrect amount for plan {plan}")

        # Save to database
        data = dict(
                amount=amount,
                currency=currency,
                channel=channel,
                user_id = user.id,
                plan=plan_name
            )
        prefs = user_db.get_prefs(user.id)
        current_credits = prefs.get("credits", 0)
        new_credits = current_credits + pplan["credits"]
        user_db.update_prefs(user.id, {"credits": new_credits})
        await Subscription.create(Subscription.get_unique_id(), data)

        return {"status": True, "data": data}

    else:
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail="Payment was unsuccessful")
