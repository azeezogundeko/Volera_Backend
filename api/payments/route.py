import asyncio

from .model import Subscription, SubscriptionLog
from .schema import PaymentData
from .services import send_payment_acknowledgement
from config import PAYSTACK_SECRET_KEY, PAYSTACK_SECRET_KEY_TEST
from api.auth.services import get_user_by_email
from db import user_db

from httpx import AsyncClient
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Body, status, BackgroundTasks, Depends


# Load environment variables (ensure you have a .env file with PAYSTACK_SECRET_KEY set)
load_dotenv()

router = APIRouter()

class Plan:
    pro = {"price": 3000, "credits": 7000}
    starter = {"price": 1000, "credits": 3000}

    @classmethod
    def get_plan(cls, name) -> int:
        return getattr(cls, name, None)

    
@router.post("/initialize-payment")
async def initialize_payment(payment: PaymentData):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY_TEST}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": payment.email,
        "amount": payment.amount,
        # Optionally, you can add a callback_url and metadata if needed
        # "callback_url": "https://yourdomain.com/payment-callback",
        # "metadata": {"custom_field": "value"}
    }

    async with AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers, timeout=10)

    if response.status_code != 200:
        error_detail = response.json().get("message", "Payment initialization failed")
        raise HTTPException(status_code=500, detail=error_detail)

    response_data = response.json()

    # Return the access_code needed for the Paystack Popup on the frontend
    return {"access_code": response_data["data"]["access_code"], "reference":  response_data["data"]["reference"]}


@router.post('/verify-payment')
async def verify_payment(
    transaction_id: str = Body(),
    plan_name: str = Body(),
    email: str = Body(),
    b: BackgroundTasks = Depends()
):
    user = await get_user_by_email(email)
    if user is None:
        raise HTTPException(404, detail='User was not found')

    url= f"https://api.paystack.co/transaction/{transaction_id}"
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY_TEST}",
        "Content-Type": "application/json"
    }

    async with AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10)
 
    if response.status_code != 200:
        await SubscriptionLog.create(user.id, {"error": "Reference code was not found"})
        raise HTTPException(404, detail="Reference code was not found")

    res = response.json()

    if res["status"] is True:
        data = res["data"]
        amount = data["amount"]
        naira_amount = float(amount) / 100
        currency = data["currency"]
        channel = data["channel"]

        plan_name = plan_name.lstrip().split()[0]

        pplan = Plan.get_plan(plan_name)

        if pplan['price'] != naira_amount:
            await SubscriptionLog.create(user.id, {"error": "User paid incorrect amount for plan {plan_name}. Expected {pplan['price']}"})
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail=f"User paid incorrect amount for plan {plan_name}. Expected {pplan['price']}")

        # Save to database
        data = dict(
                amount=amount,
                currency=currency,
                channel=channel,
                user_id = user.id,
                plan=plan_name,
                transaction_id = transaction_id
            )
        prefs = user_db.get_prefs(user.id)
        current_credits = prefs.get("credits", 0)
        new_credits = int(current_credits) + pplan["credits"]
        tasks = [
            asyncio.to_thread(user_db.update_prefs, user.id, {"credits": new_credits}),
            asyncio.to_thread(user_db.update_labels, user.id, ["subscribed"]),
            Subscription.create(Subscription.get_unique_id(), data)
        ]

        await asyncio.gather(*tasks)

        send_payment_acknowledgement(transaction_id, naira_amount, new_credits, email, b)


        return {"status": True, "data": data}

    else:
        await SubscriptionLog.create(user.id, {"error": "Payment was unsuccessful"})
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail="Payment was unsuccessful")
