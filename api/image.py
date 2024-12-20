# from fastapi import FastAPI, APIRouter, HTTPException
# from typing import Dict, Any
# from lib.providers import get_available_chat_model_providers, get_available_embedding_model_providers
# import logging

# # Initialize FastAPI app
# app = FastAPI()

# # Logger setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # API router
# router = APIRouter()

# @router.get("/")
# async def get_model_providers():
#     try:
#         # Fetch chat and embedding model providers asynchronously
#         chat_model_providers = await get_available_chat_model_providers()
#         embedding_model_providers = await get_available_embedding_model_providers()

#         # Remove 'model' field from each provider model
#         for provider in chat_model_providers.values():
#             for model in provider.values():
#                 model.pop('model', None)

#         for provider in embedding_model_providers.values():
#             for model in provider.values():
#                 model.pop('model', None)

#         # Return the model providers data
#         return {
#             "chatModelProviders": chat_model_providers,
#             "embeddingModelProviders": embedding_model_providers
#         }

#     except Exception as err:
#         logger.error(f"Error in fetching model providers: {err}")
#         raise HTTPException(status_code=500, detail="An error has occurred.")

# # Include the router in the app
# app.include_router(router, prefix="/models", tags=["models"])
