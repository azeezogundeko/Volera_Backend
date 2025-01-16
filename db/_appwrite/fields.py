from abc import ABC, abstractmethod
from typing import Optional, List, Union
from typing_extensions import Literal


class BaseField(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def to_dict(self):
        """Method to convert the field to a dictionary representation."""
        pass


class Field(BaseField):
    def __init__(
        self,
        required: bool = True,
        size: Optional[int] = None,
        array: bool = False,
        min: Optional[float] = None,
        max: Optional[float] = None,
        index_type: Optional[Literal["unique", "text", "array"]] = None,
        index_attr: Optional[Union[List[str], str]] = None,
        default: Optional[Union[str, float, list, dict]] = None,
        type: Literal["string", "datetime", "json", "array", "float", "bool", "index"] = "string",
    ):
        self.required = required
        self.size = size
        self.array = array
        self.min = min
        self.max = max
        self.type = type
        self.default = default
        self.index_type = index_type
        self.index_attr = (
            index_attr if isinstance(index_attr, list) else [index_attr] if index_attr else []
        )

    def to_dict(self):
        field = {
            "required": self.required,
            "type": self.type,
            "array": self.array,
            "default": self.default,
        }
        if self.type == "index":
            if self.index_type is None:
                raise ValueError("index_type is required when type is 'index'")
            field["index_type"] = self.index_type
            field["attributes"] = self.index_attr

        if self.type in ["string", "json"] and self.size is not None:
            field["size"] = self.size

        if self.type == "float":
            if self.min is not None:
                field["min"] = self.min
            if self.max is not None:
                field["max"] = self.max

        if self.default is not None:
            field["required"] = False

        print(field)
        return field

    def __repr__(self):
        return f"Field(required={self.required}, size={self.size}, array={self.array}, type={self.type}, min={self.min}, max={self.max}, default={self.default})"


class RelationField(BaseField):
    def __init__(
        self,
        collection_id: str,
        related_collection_id: str,
        type: Literal["one-to-one", "one-to-many", "many-to-many"],
        two_way: Optional[str] = None,
        key: Optional[str] = None,
        two_way_key: Optional[str] = None,
        on_delete: Optional[Literal["cascade", "set-null", "restrict"]] = None,
    ):
        self.collection_id = collection_id
        self.related_collection_id = related_collection_id
        self.type = type
        self.two_way = two_way
        self.key = key
        self.two_way_key = two_way_key
        self.on_delete = on_delete

    def to_dict(self):
        return {
            "collection_id": self.collection_id,
            "related_collection_id": self.related_collection_id,
            "type": self.type,
            "two_way": self.two_way,
            "key": self.key,
            "two_way_key": self.two_way_key,
            "on_delete": self.on_delete,
        }

    def __repr__(self):
        return f"RelationField(collection_id={self.collection_id}, related_collection_id={self.related_collection_id}, type={self.type}, two_way={self.two_way}, key={self.key}, two_way_key={self.two_way_key}, on_delete={self.on_delete})"


def RelationshipField(
    collection_id: str,
    related_collection_id: str,
    type: Literal["one-to-one", "one-to-many", "many-to-many"],
    two_way: Optional[str] = None,
    key: Optional[str] = None,
    two_way_key: Optional[str] = None,
    on_delete: Optional[Literal["cascade", "set-null", "restrict"]] = None,
):
    return RelationField(
        collection_id=collection_id,
        related_collection_id=related_collection_id,
        type=type,
        two_way=two_way,
        key=key,
        two_way_key=two_way_key,
        on_delete=on_delete,
    )


def AppwriteField(
    array: bool = False,
    required: bool = True,
    size: Optional[int] = None,
    min: Optional[float] = None,
    max: Optional[float] = None,
    index_attr: Optional[Union[List[str], str]] = None,
    index_type: Optional[Literal["unique", "fulltext", "key"]] = None,
    default: Optional[Union[str, float, list, dict]] = None,
    type: Literal["string", "datetime", "json", "array", "float", "bool", "index"] = "string",
) -> dict:
    return Field(
        required=required,
        size=size,
        array=array,
        type=type,
        min=min,
        max=max,
        default=default,
        index_attr=index_attr,
        index_type=index_type,
    )
