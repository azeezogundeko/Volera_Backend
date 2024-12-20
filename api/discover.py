# from fastapi import FastAPI, APIRouter, HTTPException
# import logging
# from typing import List
# from pydantic import BaseModel
# import random

# # Simulating searchSearxng function (replace this with actual search logic)
# async def search_searxng(query: str, params: dict) -> dict:
#     # Your actual search logic goes here
#     # Here, it's simulated by returning a mock result
#     return {
#         "results": [
#             {"title": f"Result for {query}", "url": f"http://example.com/{query}"}
#         ]
#     }

# # Initialize FastAPI app
# app = FastAPI()

# # Router setup
# router = APIRouter()

# # Model for the response
# class BlogResult(BaseModel):
#     title: str
#     url: str

# @router.get("/", response_model=dict)
# async def get_discover_blogs():
#     try:
#         # Perform all the search queries in parallel (using asyncio.gather)
#         search_results = await asyncio.gather(
#             search_searxng('site:businessinsider.com AI', {'engines': ['bing news'], 'pageno': 1}),
#             search_searxng('site:www.exchangewire.com AI', {'engines': ['bing news'], 'pageno': 1}),
#             search_searxng('site:yahoo.com AI', {'engines': ['bing news'], 'pageno': 1}),
#             search_searxng('site:businessinsider.com tech', {'engines': ['bing news'], 'pageno': 1}),
#             search_searxng('site:www.exchangewire.com tech', {'engines': ['bing news'], 'pageno': 1}),
#             search_searxng('site:yahoo.com tech', {'engines': ['bing news'], 'pageno': 1}),
#         )

#         # Flatten results and shuffle randomly
#         data = [result['results'] for result in search_results]
#         data_flat = [item for sublist in data for item in sublist]
#         random.shuffle(data_flat)

#         return {"blogs": data_flat}
#     except Exception as err:
#         logging.error(f"Error in discover route: {err}")
#         raise HTTPException(status_code=500, detail="An error has occurred")

# # Include the router in the app
# app.include_router(router, prefix="/discover", tags=["discover"])
