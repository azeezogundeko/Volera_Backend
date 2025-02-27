import asyncio
from api.auth.model import UserCredits
from api.payments.model import DailyUsage
from utils.logging import logger

async def check_credits(user_id: str, type: str, amount: int = None) -> tuple[bool, int]:
    """
    Checks if the user has enough credits.
    """
    cost_map = {"text": 5, "image": 10, "amount": amount}
    cost = cost_map.get(type)

    if cost is None:
        raise ValueError("Invalid type. Must be 'text' or 'image' or 'amount'.")

    credits = await UserCredits.get_or_create(user_id)
    if credits.balance < cost:
        return False, credits.balance

    return True, credits.balance - cost

async def track_credits(user_id: str, type: str, amount=None, tokens: dict = None) -> None:
    """
    Tracks credit usage and updates balances.
    """
    cost_map = {"text": 5, "image": 10, "amount": amount}
    cost = cost_map.get(type)

    if cost is None:
        raise ValueError("Invalid type. Must be 'text' or 'image'.")

    # Deduct credits atomically
    new_balance, success = await UserCredits.update_balance(user_id, -cost, f"llm_usage_{type}")
    if not success:
        raise ValueError("Insufficient credits")

    await DailyUsage.update_usage(user_id, cost)
    logger.info(f"Credits tracked for user {user_id}: cost {cost}, new balance {new_balance}") 