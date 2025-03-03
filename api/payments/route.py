import asyncio
from datetime import datetime

from .model import Subscription, SubscriptionLog, DailyUsage
from .schema import PaymentData
from .services import send_payment_acknowledgement
from config import PAYSTACK_SECRET_KEY
from api.auth.schema import UserIn
from api.auth.model import UserCredits
from db import user_db
from utils.logging import logger
from api.admin.services import system_log

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
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
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
            await SubscriptionLog.create(user.id, {"error": f"User paid incorrect amount for plan {plan_name}. Expected {pplan['price']}"})
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
        
        try:
            # Update credits atomically using the new UserCredits model
            new_balance, success = await UserCredits.update_balance(
                user.id, 
                pplan["credits"],
                transaction_type=f"payment_{plan_name}"
            )
            
            if not success:
                logger.error(f"Failed to update credits for user {user.id} after 3 retries")
                raise HTTPException(500, detail="Failed to update credits")
                        
            # Update labels and create subscription
            await asyncio.to_thread(user_db.update_labels, user.id, ["subscribed"])
            await Subscription.create(Subscription.get_unique_id(), data)
            
            
            # Log the transaction
            await system_log("transaction", amount=naira_amount)
            
            # Send acknowledgement email
            user_first_name = user.name.split("_")[0]
            send_payment_acknowledgement(user_first_name, user.email, transaction_id, naira_amount, pplan["credits"], channel)

            return {"status": True, "data": data}
            
        except Exception as e:
            logger.error(f"Payment processing error for user {user.id}: {str(e)}", exc_info=True)
            await SubscriptionLog.create(user.id, {"error": f"Payment processing error: {str(e)}"})
            raise HTTPException(500, detail="Error processing payment")

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
    
    credits = await UserCredits.get_or_create(user.id)
    credit_usage = await DailyUsage.list(
        queries=[
            query.Query.equal("user_id", user.id),
            query.Query.order_desc("$createdAt")
        ]
    )
    total_usage = 0
    credit_usage = credit_usage["documents"][:30]

    if credit_usage:
        total_usage = sum(du.total_credits_used for du in credit_usage)

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

    # current_credits = credits.balance
        
    return {
        "currentPlan": plan_name + " Plan",
        "usedCredits": total_usage, 
        "totalCredits": credits.balance + total_usage,
        "remainingCredits": credits.balance,
        "creditHistory": [
            {
                "date": du.created_at,
                "credits": du.total_credits_used
            }
            for du in credit_usage
        ]        
        }