from __future__ import annotations

from  db._appwrite.model_base import AppwriteModelBase
from db._appwrite.fields import AppwriteField
from typing import List, TypedDict, Optional
from appwrite.query import Query


class Specification(TypedDict):
    
    #collection_id = "specification"
    label: str #= AppwriteField(size=255, required=True)
    value:  str #= AppwriteField(size=255, required=True)
   # product_id: str # = AppwriteField(size=255, required=True)

# class Stores(AppwriteModelBase):
#     collection_id = "product_stores"

#     product_id: str = AppwriteField(type="string", size=255, required=True, )
#     name: str = AppwriteField(size=255, required=True, type="string")
#     price: float = AppwriteField(type="float", required=True, default=0.0)
#     link: str = AppwriteField(size=255, required=True, type="string")

class WishList(AppwriteModelBase):
    collection_id = "wishlist"

    product_id: str = AppwriteField(size=255, required=True, type="string")
    user_id: str = AppwriteField(size=255, required=True, type="string")
    product_id: str = AppwriteField(size=255, required=True, type="string")

    index: str = AppwriteField(size=255, type="index", index_attr=["user_id", "product_id"], index_type="key")

    # async def create(cls, product_id: str, user_id: str, **kwargs)-> Optional[WishList]:
    #     document = await cls.list(queries=[Query.equal("user_id", user_id), Query.equal("product_id", product_id)])
    #     if len(document["documents"]) > 0:
    #         return None
        
    #     return await super().create(**kwargs)

    @classmethod
    async def get(cls, user_id: str, product_id: str) -> Optional[WishList]:
        document = await cls.list(queries=[
            Query.equal("user_id", user_id),
            Query.equal("product_id", product_id)
        ])
        return document["documents"][0] if document["documents"] else None

class Product(AppwriteModelBase):
    collection_id = "product"

    name: str = AppwriteField(size=255, required=True, type="string")
    image: str = AppwriteField(size=255, required=True, type="string")
    current_price: float = AppwriteField(type="float", required=False,default=0.0)
    original_price: float = AppwriteField(type="float", required=False, default=0.0)
    discount: float = AppwriteField(type="float", required=True, default=0.0)
    brand: str = AppwriteField(size=255, required=True, type="string")
    reviews_count: str = AppwriteField(size=255, type="float", default=0.0)
    source: str = AppwriteField(size=255, required=True, type="string")
    url: str = AppwriteField(size=255, required=True, type="string")
    currency: str = AppwriteField(size=5, required=False, type="string", default="₦")
    ratings: float = AppwriteField(required=False, type="float", default=0.0)
    features: List[str] = AppwriteField(required=False, type="array", default=[])
    specification: List[Specification] = AppwriteField(required=False, type="array", default=[])

