import io
import asyncio
import base64
import json
# import httpx
from typing import List
import google.generativeai as genai
# from json import loads
# from PIL import Image

# from groq import Groq

from config import ApiKeyConfig

groq_api_key = ApiKeyConfig.GROQ_API_KEY

model = genai.GenerativeModel(model_name = "gemini-1.5-pro")

# def encode_image(image: Image) -> bytes:
#     buffered = io.BytesIO()
#     image.save(buffered, format="JPEG")  # Save the image to the BytesIO object
#     return buffered.getvalue()  # Return the byte data

async def image_analysis(images: List[bytes], prompt):
    contents = []
    for image in images:
        contents.append({'mime_type':'image/jpeg', 'data': base64.b64encode(image).decode('utf-8')})

    response = await asyncio.to_thread(model.generate_content, [*contents, prompt])
    try:
        # Parse the JSON response
        json_response = json.loads(response.text)
        # Return just the search query string
        return json_response.get("search_query", "")
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract query from the raw text
        text = response.text.strip()
        if '"search_query":' in text:
            # Try to extract the query value if the response is malformed JSON
            query_start = text.find('"search_query":') + len('"search_query":')
            query_end = text.find('"', query_start + 2)
            if query_end > query_start:
                return text[query_start:query_end].strip(' "')
        return text  # Return raw text as fallback

# async def analyze_image(image: bytes, prompt, is_url=False):
#     client = Groq(api_key=groq_api_key)

#     if is_url:
#         image_content = {"type": "image_url", "image_url": {"url": image}}
#     else:
#         base64_image = base64.b64encode(image).decode('utf-8')
#         image_content = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}

#     try:
#         chat_completion = await asyncio.to_thread(client.chat.completions.create, 
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": prompt},
#                         image_content,
#                     ],
#                 }
#             ],
#             model="llama-3.2-90b-vision-preview",
#         )
#         return chat_completion.choices[0].message.content
#     except Exception as e:
#         return f"Error: {str(e)}"

# async def check_content_safety(image_description):
#     client = Groq(api_key=groq_api_key)

#     try:
#         chat_completion = await asyncio.to_thread(client.chat.completions.create,
#             messages=[
#                 {"role": "system", "content": """You are a content safety classifier. Analyze the given text and determine if it contains any unsafe or inappropriate content.

#                 If the text contains any unsafe or inappropriate content, respond with "unsafe". Otherwise, respond with "safe".
#                 ### Output Format
#                 if the text contains any unsafe or inappropriate content, respond with "unsafe". Otherwise, respond with "safe".
#                 {{
#                     "result": safe/unsafe
#                 }}

#                 ### Guidance

#                  - Please ensure your response are in JSON format.
#                  - If the text contains any unsafe or inappropriate content, respond with "unsafe". Otherwise, respond with "safe".

                
#                 """},
#                 {"role": "user", "content": f"Please analyze this image description for any unsafe or inappropriate content: {image_description}"}
#             ],
#             model="llama-3.2-90b-vision-preview",
#         )
#         return chat_completion.choices[0].message.content
#     except Exception as e:
#         return f"Error: {str(e)}"

# async def process_image(image, prompt, url=None):
#         tasks = [
#             analyze_image(image, prompt),
#             check_content_safety(await analyze_image(image, prompt))
#         ]
#         results = await asyncio.gather(*tasks)
#         image_content_result = results[0]
#         valid_image = loads(results[1])
#         validity=False
#         if valid_image["result"] == "unsafe":
#             validity = False
#         else:
#             validity = True

#         print(f"Validity: {validity}, Image content: {image_content_result}")
#         return image_content_result, validity

    # if url:
    #     async with httpx.AsyncClient() as client:
    #         response = await client.get(url)
        
    #     image = Image.open(io.BytesIO(response.content))
    #     return await analyze_image(image, prompt), await check_content_safety(await analyze_image(image, prompt))
    # else:
    #     return "Please provide an image to analyze.", ""


def get_product_prompt(user_query, prompt):
    return f""" 
        PROMPT: {prompt}

        USER QUERY: {user_query}

    """
    
IMAGE_DESCRIPTION_PROMPT = """

You are an expert image analyst specializing in converting visual content into optimized search queries. Your task is to analyze the provided image alongside the user's query to generate a precise, search-engine-friendly query that will help find similar or relevant products.

INPUT FORMAT
Image: The image you want to analyze.

User Query: The user's initial query related to the image.

OUTPUT FORMAT
A JSON object containing a refined search query:
{{
"search_query": "..."
}}

GUIDELINES FOR QUERY GENERATION:
- Focus on key product features, brands, and specifications visible in the image
- Include relevant color, style, and design elements
- Use common product category terms
- Keep the query concise but descriptive (4-8 words)
- Avoid unnecessary words like "buy", "shop", "get"
- Use standard product terminology

EXAMPLES
Image: a photo of a wristwatch encoded in base64 format

User Query: "I want to buy a smartwatch"

Output: {{
"search_query": "black rectangular touchscreen smartwatch fitness tracker"
}}

"""