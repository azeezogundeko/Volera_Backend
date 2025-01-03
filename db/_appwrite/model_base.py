# from __future__ import annotations

from typing import Literal, Type, List, Dict, Optional, Union, TypeVar
from datetime import datetime
from .base import AsyncAppWriteClient
from utils.logging import logger

# T = TypeVar(name="BaseModel", bound=AppwriteModelBase)

class AppwriteModelBase:
    """Base class for Appwrite models."""
    # def __init__(self) -> None:
    id: Optional[str] = None  # Maps to $id in Appwrite
    created_at: Optional[datetime] = None  # Maps to $createdAt
    updated_at: Optional[datetime] = None  # Maps to $updatedAt
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
        return cls.from_appwrite(document)

    @classmethod
    def get_unique_id(cls) -> str:
        return cls.client.get_unique_id()


    @classmethod
    async def read(cls, document_id: str, queries: List[str] = []) -> Type["AppwriteModelBase"]:
        document = await cls.client.get_document(
            collection_id=cls.collection_id,
            document_id=document_id,
            queries=queries
        )
        return cls.from_appwrite(document)
    
    
    @classmethod
    async def list(cls, queries: List[str]) -> List[Type["AppwriteModelBase"]]:
        documents = await cls.client.list_documents(
            collection_id=cls.collection_id,
            queries=queries
        )
        total = documents["total"]
        documents = [cls.from_appwrite(document) for document in documents["documents"]]
        return {
                "total": total,
                "documents": documents
            } 
           


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

    def to_appwrite(self) -> dict:
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
    def get_schema(cls) -> List[dict]:
        return [
            {"key": key, **value}
            for key, value in cls.__annotations__.items()
            if isinstance(value, dict)
        ]


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
                for field in cls.get_schema():
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

                    elif field.get("type") == "json":
                        await cls.client.create_string_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            size=16384,  # Large size for JSON
                            required=field.get("required", False))

                    elif field.get("type") == "bool":
                        await cls.client.create_boolean_attribute(
                            cls.collection_id,
                            field["key"],
                            field["required"],
                            field["default"],
                            field["array"]
                        )
                    else:
                        await cls.client.create_string_attribute(
                            collection_id=cls.collection_id,
                            key=field["key"],
                            size=field.get("size", 255),
                            required=field.get("required", False)
                        )
                    logger.info(f'Created attribute {field["key"]} for Chats collection')
            except Exception as attr_error:
                logger.error(f'Failed to create attribute {field["key"]}: {attr_error}')
                        
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


def AppwriteField(
    required: bool = True,
    size: Optional[int] = None,
    array: bool = False,
    type: Literal["string", "datetime", "json", "array", "float"] = "string",
    min: Optional[float] = None,
    max: Optional[float] = None,
    default: Optional[Union[str, float, list, dict]] = None
) -> dict:
    """
    Constructs a field schema for Appwrite.

    Args:
        required (bool): Whether the field is required.
        size (int, optional): Maximum size of the field (applicable to 'string' and 'json' types).
        array (bool, optional): Indicates if the field is an array. Defaults to False.
        type (Literal): The type of the field ('string', 'datetime', 'json', 'array', 'float').
        min (float, optional): Minimum value for 'float' type.
        max (float, optional): Maximum value for 'float' type.
        default (Union[str, float, list, dict], optional): Default value for the field.

    Returns:
        dict: Field schema.
    """

    # Base field schema
    field = {
        "required": required,
        "type": type,
        "array": array,
        "default": default,
    }

    # Additional validations for string and json types
    if type in ["string", "json"]:
        if size is not None:
            field["size"] = size

    # Additional validations for float type
    if type == "float":
        if min is not None:
            field["min"] = min
        if max is not None:
            field["max"] = max

    # Return the constructed schema
    return field
