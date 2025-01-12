from  db._appwrite.model_base import AppwriteModelBase, AppwriteField
from typing import List, TypedDict

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


class Product(AppwriteModelBase):
    collection_id = "product"

    title: str = AppwriteField(size=255, required=True, type="string")
    title: str = AppwriteField(size=1024, required=False, type="string")
    image: str = AppwriteField(size=255, required=True, type="string")
    title: str = AppwriteField(size=255, required=True, type="string")
    url: str = AppwriteField(size=255, required=True, type="string")
    currency: str = AppwriteField(size=5, required=True, type="string", default="₦")
    ratings: float = AppwriteField(required=True, type="float", default=0.0)
    features: List[str] = AppwriteField(required=True, type="array", default=[])
    specification: List[Specification] = AppwriteField(required=True, type="array", default=[])

