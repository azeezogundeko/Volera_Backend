import asyncio

from db._appwrite.fields import AppwriteField
from db._appwrite.model_base import AppwriteModelBase
from db import user_db

class LLMCall(AppwriteModelBase):
    user_id: str = AppwriteField()
    model_name: str = AppwriteField()
    cost = AppwriteField(type="int")
    input_tokens = AppwriteField(type="int")
    output_tokens = AppwriteField(type="int")
    total_tokens = AppwriteField(type="int")


import asyncio

async def check_credits(user_id: str, type: str, amount: int = None) -> bool:
    """
    Checks if the user has enough credits and deducts the required amount.

    :param user_id: The ID of the user.
    :param type: The type of request ("text" or "image").
    :return: True if the user has enough credits, otherwise False.
    """
    cost_map = {"text": 5, "image": 10, "amount": amount}
    cost = cost_map.get(type)

    if cost is None:
        raise ValueError("Invalid type. Must be 'text' or 'image' or 'amount'.")

    # Fetch user preferences (credits balance)
    user_pref = await asyncio.to_thread(user_db.get_prefs, user_id)
    credits = user_pref.get("credits", 0)  # Default to 0 if not found
 
    if int(credits) < cost:
        return False, credits

    # # Deduct credits
    # new_credits = credits - cost
    # await asyncio.to_thread(user_db.update_prefs, user_id, {"credits": new_credits})

    return True, credits  # Sufficient credits and deduction successful


async def track_llm_call(user_id: str, type: str, amount=None, tokens: dict = None) -> None:
    """
    Tracks an LLM call, logs usage details, and deducts user credits.

    :param user_id: The ID of the user making the request.
    :param model: The name of the LLM model used.
    :param type: The type of request ("text" or "image").
    :param tokens: A dictionary containing token usage details.
    """

    cost_map = {"text": 5, "image": 10, "amount": amount}
    cost = cost_map.get(type)

    if cost is None:
        raise ValueError("Invalid type. Must be 'text' or 'image'.")

    tokens = tokens or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    data = {
        "user_id": user_id,
        # "model_name": model,
        "input_tokens": tokens.get("input_tokens", 0),
        "output_tokens": tokens.get("output_tokens", 0),
        "total_tokens": tokens.get("total_tokens", 0),
        "cost": cost,
    }

    # Log the LLM call
    # await LLMCall.create(LLMCall.get_unique_id(), data=data)

    # Deduct credits (ensuring user has enough)
    user_pref = await asyncio.to_thread(user_db.get_prefs, user_id)
    credits = user_pref.get("credits", 0)

    new_credits = int(credits) - cost
    await asyncio.to_thread(user_db.update_prefs, user_id, {"credits": new_credits})
