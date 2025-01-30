import asyncio
import inspect
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from config import (
    ApiKeyConfig,  
    APPWRITE_DATABASE_ID, 
    APPWRITE_ENDPOINT, 
    APPWRITE_PROJECT_ID,
    APPWRITE_BUCKET_ID
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
        self.bucket_id = APPWRITE_BUCKET_ID

        self.database = Databases(self.client)
        self.storage = Storage(self.client)
        self.users = Users(self.client)
        self._executor = ThreadPoolExecutor(max_workers=10)

    def get_unique_id(self):
        return ID.unique()

    # async def create_bucket(
    #     self, 
    #     bucket_id, 
    #     name, 
    #     permissions = None, 
    #     file_security = None, 
    #     enabled = None, 
    #     maximum_file_size = None, 
    #     allowed_file_extensions = None, 
    #     compression = None, 
    #     encryption = None, 
    #     antivirus = None
    #     ):
    #     return await self._run_in_executor(
    #         self.storage.create_bucket,
    #         bucket_id, name, permissions, file_security, enabled, maximum_file_size, allowed_file_extensions, compression, encryption, antivirus
    #     )

    async def create_file(self, file_id, file, permissions = None, on_progress = None):
        return await self._run_in_executor(
            self.storage.create_file,
            self.bucket_id, file_id, file, permissions, on_progress

        )

    async def get_file(self, file_id):
        return await self._run_in_executor(
            self.storage.get_file_download,
            self.bucket_id, file_id
        )
    async def get_file_metadata(self, file_id):
        return await self._run_in_executor(
            self.storage.get_file,
            self.bucket_id, file_id
        )

    async def update_file(self, file_id, file, permissions = None, on_progress = None):
        return await self._run_in_executor(
            self.storage.update_file,
            self.bucket_id, file_id, file, permissions, on_progress
        )

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

    async def set_relationship(
        self, collection_id, related_collection_id, type, two_way = None, key = None, two_way_key = None, on_delete = None):
        return await self._run_in_executor(
            self.database.create_relationship_attribute,
            self.database_id, collection_id, related_collection_id, type, two_way, key, two_way_key, on_delete
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
    async def create_float_attribute(
        self, collection_id, key, required, min=None, max=None, default=None, array=None):
            return await self._run_in_executor(
                self.database.create_float_attribute,
                self.database_id,
                collection_id,
                key,
                required,
                min,
                max,
                default,
                array
            )

    async def create_integer_attribute(
        self, collection_id, key, required, min=None, max=None, default=None, array=None):
            return await self._run_in_executor(
                self.database.create_integer_attribute,
                self.database_id,
                collection_id,
                key,
                required,
                min,
                max,
                default,
                array
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

    async def create_boolean_attribute(
        self, collection_id, key: str, required=True, default=None, array = None
    ):
        return await self._run_in_executor(
            self.database.create_boolean_attribute,
            self.database_id,
            collection_id,
            key,
            required,
            default,
            array
        )

    async def create_index(
        self, collection_id, key, type, attributes, order = None
    ):
        return self._run_in_executor(
            self.database.create_index,
            self.database_id,
            collection_id,
            key,
            type,
            attributes,
            order
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


class AsyncUsersWrapper(Users):
    def __init__(self):
        self.client = AsyncAppWriteClient()
        super().__init__(self.client)
        self._executor = ThreadPoolExecutor(max_workers=10)


    def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(
            self._executor, 
            func, 
            *args, 
            **kwargs
        )

    def __getattr__(self, name):
        # Check if the method exists in the sync class
        sync_method = getattr(super(), name)

        # If it's callable, wrap it in an async function
        if callable(sync_method):
            async def async_method(*args, **kwargs):
                return await self._run_in_executor(sync_method, *args, **kwargs)
            return async_method
        else:
            # If it's not a callable method (e.g., an attribute), return it directly
            return sync_method

    def __dir__(self):
        # Use inspect to get all methods of the SyncClass
        sync_methods = inspect.getmembers(self.sync_class_instance, predicate=inspect.ismethod)
        # Return the list of method names from the SyncClass instance
        return [method[0] for method in sync_methods]


