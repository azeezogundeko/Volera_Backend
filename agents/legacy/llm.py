import asyncio

from db._appwrite.fields import AppwriteField
from db._appwrite.model_base import AppwriteModelBase
# from db import user_db
# from api.payments.services import record_credit_transaction
# from api.auth.model import UserCredits
# from api.payments.model import DailyUsage
# from utils.logging import logger
from api.auth.credit_manager import check_credits, track_credits as track_llm_call

class LLMCall(AppwriteModelBase):
    user_id: str = AppwriteField()
    model_name: str = AppwriteField()
    cost = AppwriteField(type="int")
    input_tokens = AppwriteField(type="int")
    output_tokens = AppwriteField(type="int")
    total_tokens = AppwriteField(type="int")



# async def check_credits(user_id: str, type: str, amount: int = None) -> bool:
#     """
#     Checks if the user has enough credits and deducts the required amount.

#     :param user_id: The ID of the user.
#     :param type: The type of request ("text" or "image").
#     :return: True if the user has enough credits, otherwise False.
#     """
#     cost_map = {"text": 5, "image": 10, "amount": amount}
#     cost = cost_map.get(type)

#     if cost is None:
#         raise ValueError("Invalid type. Must be 'text' or 'image' or 'amount'.")

#     # Fetch user preferences (credits balance)
#     credits = await UserCredits.get_or_create(user_id)

#     if credits.balance < cost:
#         return False, credits.balance

#     return True, credits.balance - cost


# async def track_llm_call(user_id: str, type: str, amount: int, tokens: int):
#     """Track LLM call and deduct credits"""
#     try:
#         cost_map = {
#             "text": 1,
#             "image": 5
#         }
        
#         # Deduct credits atomically
#         cost = cost_map[type] * tokens
#         new_balance, success = await UserCredits.update_balance(
#             user_id, 
#             -cost,
#             f"llm_usage_{type}"  # Transaction type for LLM usage
#         )
        
#         if not success:
#             logger.error(f"Failed to deduct {cost} credits for user {user_id}")
#             return False

# #     data = {
# #         "user_id": user_id,
# #         "input_tokens": tokens.get("input_tokens", 0),
# #         "output_tokens": tokens.get("output_tokens", 0),
# #         "total_tokens": tokens.get("total_tokens", 0),
# #         "cost": cost,
# #     }

#         logger.info(f"Deducted {cost} credits for {type} LLM call. New balance: {new_balance}")
#         return True

#     except Exception as e:
#         logger.error(f"Error tracking LLM call: {str(e)}")
#         return False


# #     # await asyncio.gather(*tasks)
# #     logger.info(f"LLM call tracked for user {user_id}: cost {cost}, new balance {new_balance}")
