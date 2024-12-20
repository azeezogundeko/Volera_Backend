# from fastapi import FastAPI, APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import List, Optional
# import logging
# from langchain.core.language_models.chat_models import BaseChatModel
# from langchain.core.messages import HumanMessage, AIMessage
# from langchain.openai import ChatOpenAI
# from lib.providers import get_available_chat_model_providers
# from chains.agents.video_search_agent import handle_video_search

# # Initialize FastAPI app
# app = FastAPI()

# # Logger setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # API router
# router = APIRouter()

# # Request body models
# class ChatModel(BaseModel):
#     provider: str
#     model: str
#     customOpenAIBaseURL: Optional[str] = None
#     customOpenAIKey: Optional[str] = None

# class VideoSearchBody(BaseModel):
#     query: str
#     chatHistory: List[dict]
#     chatModel: Optional[ChatModel] = None

# # Video search route
# @router.post("/")
# async def video_search(body: VideoSearchBody):
#     try:
#         # Convert chat history to appropriate message objects
#         chat_history = [
#             HumanMessage(msg["content"]) if msg["role"] == "user" else AIMessage(msg["content"])
#             for msg in body.chatHistory
#         ]

#         # Fetch available chat model providers
#         chat_model_providers = await get_available_chat_model_providers()

#         # Select chat model provider and model
#         chat_model_provider = body.chatModel.provider if body.chatModel else list(chat_model_providers.keys())[0]
#         chat_model = body.chatModel.model if body.chatModel else list(chat_model_providers[chat_model_provider].keys())[0]

#         llm: Optional[BaseChatModel] = None

#         if body.chatModel and body.chatModel.provider == "custom_openai":
#             if not body.chatModel.customOpenAIBaseURL or not body.chatModel.customOpenAIKey:
#                 raise HTTPException(status_code=400, detail="Missing custom OpenAI base URL or key")

#             # Create OpenAI model instance for custom OpenAI API
#             llm = ChatOpenAI(
#                 model_name=body.chatModel.model,
#                 openai_api_key=body.chatModel.customOpenAIKey,
#                 temperature=0.7,
#                 configuration={"base_url": body.chatModel.customOpenAIBaseURL}
#             )
#         elif (
#             chat_model_provider in chat_model_providers and 
#             chat_model in chat_model_providers[chat_model_provider]
#         ):
#             llm = chat_model_providers[chat_model_provider][chat_model].model

#         if not llm:
#             raise HTTPException(status_code=400, detail="Invalid model selected")

#         # Handle the video search
#         videos = await handle_video_search(
#             {"query": body.query, "chat_history": chat_history},
#             llm
#         )

#         return {"videos": videos}

#     except Exception as err:
#         logger.error(f"Error in video search: {err}")
#         raise HTTPException(status_code=500, detail="An error has occurred.")

# # Include the router in the app
# app.include_router(router, prefix="/video-search", tags=["video-search"])
