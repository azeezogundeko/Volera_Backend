from __future__ import annotations

from typing import Type, List, Dict, Optional, Any #, TypeVar
from datetime import datetime
from appwrite.client import AppwriteException
from .base import AsyncAppWriteClient
from utils.logging import logger
from .fields import BaseField #, Field

from appwrite.query import Query

# T = TypeVar('T', bound=AppwriteModelBase)


class AppwriteModelBase:
    """Base class for Appwrite models."""
    # def __init__(self) -> None:
    id: Optional[str] = None  # Maps to $id in Appwrite
    created_at: Optional[datetime] = None  # Maps to $createdAt
    updated_at: Optional[datetime] = None  # Maps to $updatedAt

    owner_id: Optional[str] = None
    tags: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    custom_metadata: Optional[Dict[str, Any]] = None
    # metadata: Optional[Dict[str, Any]] = None  # Additional metadata

    client = AsyncAppWriteClient()
    _registered_models: Dict[str, Type["AppwriteModelBase"]] = {}

    collection_id: str
    _fields: dict = {}


    @classmethod
    async def create(cls, document_id: str, data: dict) -> Type["AppwriteModelBase"]:
        document = await cls.client.create_document(
            collection_id=cls.collection_id,
            document_id=document_id,
            document_data=data,            
        )
        # try:
        #     document = await client.get_document(
        #         collection_id=CollectionMetadata.collection_id,
        #         document_id=cls._registered_models[cls.__name__].collection_id
        #     )
        # except AppwriteException as e:
        #     document = await client.create_document(
        #         collection_id=CollectionMetadata.collection_id,
        #         document_id=cls._registered_models[cls.__name__].collection_id,
        #         document_data={
        #             "collection_name": cls._registered_models[cls.__name__].collection_name,
        #             "description": cls._registered_models[cls.__name__].description,
        #             "no_of_items": 0,
        #             "created_at": datetime.now(timezone.utc),
        #             "updated_at": datetime.now(timezone.utc),
        #             "owner_id": cls._registered_models[cls.__name__].owner_id,
        #             "status": cls._registered_models[cls.__name__].status,
        #             "tags": cls._registered_models[cls.__name__].tags,
        #             "visibility": cls._registered_models[cls.__name__].visibility,
        #             "thumbnail_url": cls._registered_models[cls.__name__].thumbnail_url,
        #             "custom_metadata": cls._registered_models[cls.__name__].custom_metadata
        #         }
        #     )
        # document = await client.update_document(
        #     collection_id=CollectionMetadata.collection_id,
        #     document_id=cls._registered_models[cls.__name__].collection_id,
        #     data={
        #         "no_of_items": document["no_of_items"] + 1,
        #         "updated_at": datetime.now(timezone.utc)
        #     }
        # )
        return cls.from_appwrite(document)


    @classmethod
    async def get_or_create(cls, document_id: str, data: dict)-> Optional[Type["AppwriteModelBase"]]:
        try:
            document = await cls.read(document_id)
        except AppwriteException:
            return await cls.create(document_id, data)
        return document

    # @classmethod
    # async def get_or_400(cls, document_id: str, **kwargs)-> Optional[Type["AppwriteModelBase"]]:
    #     document = await cls.read(document_id)

    #     if document is not None:
    #         raise Exception("Item already exists")
            
    #     return document

    @classmethod
    def hash(cls, value: str) -> str:
        import hashlib

        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:30]


    @classmethod
    def get_unique_id(cls) -> str:
        return cls.client.get_unique_id()

    @classmethod
    async def create_file(cls, file_id, file, permissions = None, on_progress = None):
        return await cls.client.create_file(file_id, file, permissions, on_progress)
    
    @classmethod
    async def update_file(cls, file_id, file, permissions = None, on_progress = None):
        return await cls.client.update_file(file_id, file, permissions, on_progress)

    @classmethod
    async def get_file(cls, file_id):
        return await cls.client.get_file(file_id)
        
    @classmethod
    async def get_file_metadata(cls, file_id):
        return await cls.client.get_file_metadata(file_id)


    @classmethod
    async def read(cls, document_id: str, queries: List[str] = []) -> Type["AppwriteModelBase"]:
        # queries.append(Query.equal("is_deleted", False))
        document = await cls.client.get_document(
            collection_id=cls.collection_id,
            document_id=document_id,
            queries=queries
        )
        return cls.from_appwrite(document)
    
    
    @classmethod
    async def list(cls, queries: List[str] = [], limit: int = 25, offset: int = 0) -> List[Type["AppwriteModelBase"]]:
        queries.extend(
            [
                # Query.equal("is_deleted", False),
                Query.limit(limit),
                Query.offset(offset)
            ]
        )
        try:
            documents = await cls.client.list_documents(
                collection_id=cls.collection_id,
                queries=queries
            )
        except AppwriteException:
            return {"total": 0, "documents": []}
        total = documents["total"]
        documents = [cls.from_appwrite(document) for document in documents["documents"]]
        return {
                "total": total,
                "documents": documents
            } 


    @classmethod
    async def count(cls, queries: List[str] = []) -> int:
        count = 0
        limit = 100
        cursor = None

        while True:
            # Add dynamic queries for pagination
            dynamic_queries = queries + [Query.limit(limit)]
            if cursor:
                dynamic_queries.append(Query.cursor_after(cursor))

            # Remove None from queries
            dynamic_queries = [q for q in dynamic_queries if q is not None]

            # Fetch a page of documents
            try:
                page = await cls.client.list_documents(
                    collection_id=cls.collection_id,
                    queries=dynamic_queries,
                )
            except AppwriteException as e:
                print(e)
                if e.code == 404:
                    return count
                raise e
            documents = page.get("documents", [])

            if not documents:  # Break the loop if no more documents
                return 0

            count += len(documents)

            if len(documents) < limit:  # Stop if fewer documents than limit
                break

            # Update cursor to the last document's ID
            cursor = documents[-1]["$id"]

        return count


    # @classmethod
    # async def count(cls, queries: List[str] = []):
    #     docs = await cls.list(queries)
    #     return docs["total"]

    @classmethod
    async def update(cls, document_id: str, data: dict) -> Type["AppwriteModelBase"]:
        document = await cls.client.update_document(
            collection_id=cls.collection_id,
            document_id=document_id,
            document_data=data,
        )
        return cls.from_appwrite(document)


    @classmethod
    async def delete(cls, document_id: str) -> None:
        return await cls.client.delete_document(
            collection_id=cls.collection_id,
            document_id=document_id,
        )


    @classmethod
    def validate(cls, data: dict) -> None:
        """
        Validates the input data against the defined schema.

        Raises:
            ValueError: If validation fails.
        """
        for field_name, field_properties in cls.__annotations__.items():
            if field_properties.get("required") and field_name not in data:
                raise ValueError(f"Missing required field: {field_name}")
            if field_name in data and len(str(data[field_name])) > field_properties.get("size", 0):
                raise ValueError(f"Field '{field_name}' exceeds maximum size {field_properties['size']}.")


    @classmethod
    def from_appwrite(cls, document: dict)-> Type["AppwriteModelBase"]:
        """Create an instance from an Appwrite document."""
        instance = cls()
        instance .__dict__.update(document)
        instance.id = document.get('$id')
        instance.created_at = document.get('$createdAt')
        instance.updated_at = document.get('$updatedAt')
        # instance.metadata = document.get('metadata', {})
        return instance

    def to_dict(self) -> dict:
        """Convert the instance to a format compatible with Appwrite."""
        data = self.__dict__.copy()
        data['$id'] = data.pop('id', None)
        data['$createdAt'] = data.pop('created_at', None)
        data['$updatedAt'] = data.pop('updated_at', None)
        # data['metadata'] = data.pop('metadata', {})
        return data

    @staticmethod
    def build_query(filters: dict) -> List[str]:
        """
        Builds Appwrite-compatible query strings.

        Args:
            filters: A dictionary of field-value pairs to filter by.

        Returns:
            A list of query strings.
        """
        return [f"{field}=={value}" for field, value in filters.items()]


    @classmethod
    def register_field(cls, field_name: str, field_properties: dict) -> None:
        """Registers a field for the model schema."""
        cls._fields[field_name] = field_properties


    @classmethod
    def get_schema(cls):
        dict_fields = []
        
        for name, value in cls.__dict__.items():
            # Check if the field is an instance of AppwriteField
            if isinstance(value, BaseField):
                dict_fields.append({"key":name, **value.to_dict()})

        # dict_fields.append({"key": "is_deleted", "value": {"required": True, "type": "bool", "default": False}})
        return dict_fields


    @classmethod
    async def create_collection(cls, model_name) -> None:
        try:
            await  cls.client.get_collection(cls.collection_id)
            logger.info(f'{model_name} collection already exists')
        except Exception as e:
            logger.warning(f'Attempting to create {model_name}: {e}')
            await cls.client.create_collection(
                collection_id=cls.collection_id,
                name=model_name,
                # permission="document",
                # read=["*"],  # Update as needed
                # write=["*"],  # Update as needed
            )

            logger.info(f'Created collection {model_name}')
            try:
                schema = cls.get_schema()
                for field in schema:
                    if field.get("type") == "array":
                        await cls.client.create_string_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            size=field.get("size", 16384),  # Default size for arrays
                            required=field.get("required", False),
                            array=True)

                    elif field.get("type") == "datetime":
                        await cls.client.create_datetime_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            required=field.get("required", False))

                    elif field.get("type") == "float":
                        await cls.client.create_float_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            required=field.get("required", False),
                            min=field.get("min", None),
                            max=field.get("max", None),
                            default=field.get("default", None),
                            array=field.get("array", None)
                            )
                    elif field.get("type") == "int":
                        await cls.client.create_integer_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            required=field.get("required", False),
                            min=field.get("min", None),
                            max=field.get("max", None),
                            default=field.get("default", None),
                            array=field.get("array", None)
                            )

                    elif field.get("type") == "index":
                        await cls.client.create_index(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            type=field["index_type"],
                            attributes=field["attributes"],
                            order=field.get("order", None)
                        )

                    elif field.get("type") == "json":
                        await cls.client.create_string_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            size=16384,  # Large size for JSON
                            required=field.get("required", False),
                            array=field["array"],
                            default=field["default"],
                            )

                    elif field.get("type") == "bool":
                        await cls.client.create_boolean_attribute(
                            cls.collection_id,
                            field["key"],
                            field["required"],
                            field["default"],
                            field["array"]
                        )
                    
                    elif field.get("type") == "string":
                        await cls.client.create_string_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            size=field.get("size", 255),
                            required=field.get("required", False)
                        )
                    else:
                        logger.error(f"Unknown field type: {field['value']['type']}")

                    logger.info(f'Created attribute {field["key"]} for {cls.collection_id} collection')
            except AppwriteException as e:
                print(e.message)
                logger.error(f'Failed to create attribute {field["key"]}: {e}')
                        
        except Exception as e:
            print(f"Failed to create collection '{collection_name}': {e}")  


    @classmethod
    async def bulk_create(cls, documents: List[Type["AppwriteModelBase"]]) -> None:
        await cls.bulk_create(documents)
        print(f"Created {len(documents)} documents in bulk.")


    @classmethod
    def register_model(cls, model: Type["AppwriteModelBase"]):
        """
        Register a model with AppwriteModelBase.
        """
        if not  hasattr(model, "collection_id"):
            raise ValueError(f"Model {model.__name__} must define 'database_id' and 'collection_id' attributes.")
        
        if not hasattr(model, "get_schema"):
            raise ValueError(f"Model {model.__name__} must implement 'get_schema' method.")
        
        cls._registered_models[model.__name__] = model
        logger.info(f"Registered model: {model.__name__}")

    @classmethod
    def get_registered_models(cls) -> List[str]:
        """
        Get a list of all registered model names.
        """
        return list(cls._registered_models.keys())

    @classmethod
    async def create_all_collections(cls):
        """
        Create collections for all registered models.
        """
        for model_name, model in cls._registered_models.items():
            await model.create_collection(model_name)



# T = TypeVar(name="BaseModel", bound=AppwriteModelBase)
# class CollectionMetadata:
#     collection_id = "collection_metadata"

#     collection_name: str = AppwriteField(size=255, required=True, type="string")
#     description: str = AppwriteField(size=255, required=True, type="string")
#     no_of_items: int = AppwriteField(required=True, type="int", default=0)
#     created_at: datetime = AppwriteField(required=True, type="datetime", default=datetime.now(timezone.utc))
#     updated_at: datetime = AppwriteField(required=True, type="datetime", default=datetime.now(timezone.utc))
#     owner_id: str = AppwriteField(required=True, type="string")
#     status: str = AppwriteField(required=True, type="string", default="active")
#     tags: List[str] = AppwriteField(required=False, type="array")
#     visibility: str = AppwriteField(required=True, type="string", default="public")
#     thumbnail_url: str = AppwriteField(required=False, type="string")
#     custom_metadata: dict = AppwriteField(required=False, type="json")
