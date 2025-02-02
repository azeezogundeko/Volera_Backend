import asyncio

from .model import Subscription, SubscriptionLog, DailyUsage
from .schema import PaymentData
from .services import send_payment_acknowledgement, record_credit_transaction
from config import PAYSTACK_SECRET_KEY, PAYSTACK_SECRET_KEY_TEST
from api.auth.schema import UserIn
from db import user_db
from utils.logging import logger

from httpx import AsyncClient
from appwrite import query
from fastapi import APIRouter, HTTPException, Body, status, BackgroundTasks, Request



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
    request: Request,
    b: BackgroundTasks,
    transaction_id: str = Body(),
    plan_name: str = Body(),
    email: str = Body(),
):
    user: UserIn = request.state.user
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
                amount=naira_amount,
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
            Subscription.create(Subscription.get_unique_id(), data),
            record_credit_transaction(user.id, pplan["credits"])
        ]

        await asyncio.gather(*tasks)
        user_first_name = user.name.split("_")[0]
        send_payment_acknowledgement(user_first_name, user.email, transaction_id, naira_amount, pplan["credits"], channel, b)

        return {"status": True, "data": data}

    else:
        await SubscriptionLog.create(user.id, {"error": "Payment was unsuccessful"})
        raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, detail="Payment was unsuccessful")


@router.get("/billing/info")
async def get_billing_data(
    request: Request,
):
    user = request.state.user
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    prefs = user_db.get_prefs(user.id)
    credit_usage = await DailyUsage.list(
        queries=[
            query.Query.equal("user_id", user.id),
            query.Query.order_desc("$createdAt")
        ]
    )
    total_usage = 0
    credit_usage = credit_usage["documents"][:30]

    if credit_usage:
        total_usage = sum(du.total_credits for du in credit_usage)

    plan = await Subscription.list(
        queries=[
            query.Query.equal("user_id", user.id),
            query.Query.order_desc("$createdAt")
        ],
        limit=1
    )


    if plan["total"] == 0:
        plan_name = "Free"
    else:
        plan_name = plan["documents"][0].plan.upper()

    current_credits = prefs.get("credits", 0)
        
    return {
        "currentPlan": plan_name + " Plan",
        "usedCredits": total_usage, 
        "totalCredits": total_usage + current_credits,
        "remainingCredits": current_credits,
        "creditHistory": [
            {
                "date": du.created_at,
                "credits": du.total_credits
            }
            for du in credit_usage
        ]        
        }