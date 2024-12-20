# import os
# import logging
# import shutil
# import uuid
# from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
# from fastapi.responses import JSONResponse
# from typing import List, Optional
# from pydantic import BaseModel
# from langchain.embeddings import Embeddings
# from langchain.document_loaders import PDFLoader, DocxLoader
# from langchain.textsplitters import RecursiveCharacterTextSplitter
# from langchain.document import Document
# import aiofiles

# # Initialize FastAPI app
# app = FastAPI()

# # Logger setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Recursive character text splitter (configurable chunk size)
# splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)

# # Helper function to handle file uploads
# def save_file(file: UploadFile, upload_dir: str) -> str:
#     file_location = os.path.join(upload_dir, f"{uuid.uuid4().hex}-{file.filename}")
#     with open(file_location, "wb") as f:
#         shutil.copyfileobj(file.file, f)
#     return file_location

# # Embedding model (placeholder for actual embedding model selection logic)
# async def get_embeddings_model(model_name: str) -> Embeddings:
#     # Load your embeddings model here based on the model_name
#     return Embeddings()

# # API router
# router = APIRouter()

# # Pydantic model for embedding and file input validation
# class EmbeddingRequest(BaseModel):
#     embedding_model: str
#     embedding_model_provider: str

# class FileInfo(BaseModel):
#     file_name: str
#     file_extension: str
#     file_id: str

# @router.post("/upload", response_model=dict)
# async def upload_files(
#     files: List[UploadFile] = File(...),
#     embedding_model: str = "default_model",
#     embedding_model_provider: str = "default_provider",
# ):
#     try:
#         upload_dir = "./uploads"
#         os.makedirs(upload_dir, exist_ok=True)

#         # Validate embedding model and provider
#         embeddings_model = await get_embeddings_model(embedding_model)
#         if not embeddings_model:
#             raise HTTPException(status_code=400, detail="Invalid LLM model selected")

#         file_info = []
#         for file in files:
#             # Save file to disk
#             file_location = save_file(file, upload_dir)

#             # Load document based on file type
#             docs = []
#             if file.content_type == "application/pdf":
#                 loader = PDFLoader(file_location)
#                 docs = await loader.load()
#             elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
#                 loader = DocxLoader(file_location)
#                 docs = await loader.load()
#             elif file.content_type == "text/plain":
#                 async with aiofiles.open(file_location, 'r') as f:
#                     text = await f.read()
#                 docs = [Document(page_content=text, metadata={"title": file.filename})]

#             # Split documents into smaller chunks
#             splitted_docs = await splitter.split_documents(docs)

#             # Save extracted text into JSON file
#             extracted_json_path = file_location.replace(".", "-extracted.json")
#             with open(extracted_json_path, "w") as f:
#                 json_data = {
#                     "title": file.filename,
#                     "contents": [doc.page_content for doc in splitted_docs]
#                 }
#                 json.dump(json_data, f)

#             # Generate embeddings for the document chunks
#             embeddings = await embeddings_model.embed_documents([doc.page_content for doc in splitted_docs])

#             # Save embeddings into JSON file
#             embeddings_json_path = file_location.replace(".", "-embeddings.json")
#             with open(embeddings_json_path, "w") as f:
#                 embeddings_data = {
#                     "title": file.filename,
#                     "embeddings": embeddings
#                 }
#                 json.dump(embeddings_data, f)

#             # Collect file info for response
#             file_info.append({
#                 "file_name": file.filename,
#                 "file_extension": file.filename.split(".")[-1],
#                 "file_id": file_location.split(os.sep)[-1].split(".")[0]
#             })

#         return {"files": file_info}

#     except Exception as err:
#         logger.error(f"Error during file upload: {err}")
#         raise HTTPException(status_code=500, detail="An error occurred during the file upload")

# # Include the router in the app
# app.include_router(router, prefix="/files", tags=["files"])
