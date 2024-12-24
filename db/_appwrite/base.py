import asyncio
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from config import (
    ApiKeyConfig,  
    APPWRITE_DATABASE_ID, 
    APPWRITE_ENDPOINT, 
    APPWRITE_PROJECT_ID
    )

from appwrite.id import ID
# from appwrite.query import Query
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.storage import Storage
from appwrite.services.databases import Databases


class AsyncAppWriteClient:
    def __init__(self):
        self.client = Client()
        self.client.set_project(APPWRITE_PROJECT_ID)
        self.client.set_key(ApiKeyConfig.APPWRITE_API_KEY)
        self.client.set_endpoint(APPWRITE_ENDPOINT)
        self.database_id = APPWRITE_DATABASE_ID

        self.database = Databases(self.client)
        self.storage = Storage(self.client)
        self.users = Users(self.client)
        self._executor = ThreadPoolExecutor(max_workers=10)
        # self.initialize_collection(["jobs", "users", "cv_metadata", "scholarships", "internships"])

    def get_unique_id(self):
        return ID.unique()

    def _run_in_executor(self, func, *args, **kwargs):
        """
        Run a blocking operation in a thread pool.
        
        Args:
            func (callable): Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
        
        Returns:
            Result of the function
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._executor, 
            func, 
            *args, 
            **kwargs
        )
    async def create_document(
        self, 
        collection_id: str, 
        document_data: Dict[str, Any], 
        document_id: Optional[str] = None) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.create_document,
            self.database_id,  collection_id,  document_id or ID.unique(), document_data
        )

    async def list_documents(
        self, 
        collection_id: str, 
        queries: Optional[List[str]] = None
        ) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.list_documents,
            self.database_id, collection_id, queries or []
        )

    async def get_document(
        self, 
        collection_id,
        document_id: str, 
        queries: Optional[List[str]] = None
        ) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.get_document,
            self.database_id, collection_id,document_id, queries or []
        )

    async def upload_file(
        self, 
        bucket_id: str, 
        file_path: str, 
        file_name: Optional[str] = None
        ) -> Dict[str, Any]:
        with open(file_path, 'rb') as file:
            return await self._run_in_executor(
                self.storage.create_file,
                bucket_id, 
                ID.unique(), 
                file
            )

    async def delete_document(
        self, 
        collection_id: str, 
        document_id: str) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.delete_document,
            self.database_id, 
            collection_id, 
            document_id
        )

    async def update_document(
        self, collection_id: str, document_id: str, document_data: Dict[str, Any]) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.update_document,
            self.database_id, 
            collection_id, 
            document_id, 
            document_data
        )

    async def create_string_attribute(
        self, collection_id, key, size, required, default = None,  array = None,  encrypt = None
        ):
                      
        return await self._run_in_executor(
            self.database.create_string_attribute,
            self.database_id, collection_id, key, size, required, default, array, encrypt
        )

    async def create_datetime_attribute(
        self, collection_id, key, required, default = None, array = None
    ):
        return await self._run_in_executor(
            self.database.create_datetime_attribute,
            self.database_id, collection_id, key, required, default, array
        )

    async def create_collection(
        self, 
        collection_id: str, 
        name: str, 
        permissions: Optional[List[str]] = None) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.database.create_collection,
            self.database_id, collection_id, name, permissions or []
        )

    async def get_collection(self, collection_id) -> Dict[str, Any]:
        # Ensure collection_id is a string
        if not isinstance(collection_id, str):
            logger.error(f"Invalid collection_id type: {type(collection_id)}, value: {collection_id}")
            raise ValueError(f"Collection ID must be a string, not {type(collection_id)}")
        
        return await self._run_in_executor(
            self.database.get_collection,
            self.database_id,
            collection_id
        )

    async def list_collections(self, collection_id) -> Dict[str, Any]:
        
        return await self._run_in_executor(
            self.database.list_collections,
            self.database_id
            )

    async def create_user(
        self, 
        user_id: str, 
        email: str, 
        password: str, 
        name: Optional[str] = None) -> Dict[str, Any]:

        return await self._run_in_executor(
            self.users.create_bcrypt_user,
            user_id,
            email,
            password,
            name
        )

    async def initialize_collection(
        self, 
        collection_names: List[str], 
        permissions: Optional[List[str]] = None
        ) -> List[Dict[str, Any]]:
        results = []
        for collection_name in collection_names:
            try:
                collection = await self.create_collection(
                    collection_id=collection_name,
                    name=collection_name,
                    permissions=permissions
                )
                results.append(collection)
            except Exception as e:
                print(f"Error creating collection {collection_name}: {e}")
        return results

# Singleton instance
async_appwrite = AsyncAppWriteClient()
