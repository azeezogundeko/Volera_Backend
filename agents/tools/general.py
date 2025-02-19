from typing import Dict, Any
from api.product.services import list_products, save_product
from api.product.schema import ProductDetail
from api.auth.services import get_user_by_id
from api.auth.model import UserPreferences
from api.track.model import TrackedItem
from db.cache.dict import DiskCacheDB
from utils.ecommerce_manager import EcommerceManager
from config import DB_PATH

from api.track.scrape import scraper

# Function to initialize EcommerceManager at runtime
def get_ecommerce_manager() -> EcommerceManager:
    if not hasattr(get_ecommerce_manager, "_instance"):
        get_ecommerce_manager._instance = EcommerceManager(DiskCacheDB(cache_dir=str(DB_PATH)))
    return get_ecommerce_manager._instance

async def search_product_list(user_id: str, optimized_query: str, n_results: int = 25) -> Dict[str, Any]:
    """
    Search for products and return a list of results.
    """
    ecommerce_manager = get_ecommerce_manager()
    products = await list_products(
        ecommerce_manager,
        user_id="666666666666666666666666",
        query=optimized_query,
        max_results=3,
        limit=n_results
    )
    return products

async def save_product_to_waishlist(product_id: str, user_id: str) -> str:
    """
    Save a product to the user's waitlist.
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return "Unsuccessful: User not found"

        ecommerce_manager = get_ecommerce_manager()
        product = await ecommerce_manager.get_product_detail(product_id)
        product_data = ProductDetail.model_dump(product)
        await save_product(product_data, user)

        return "Successful"
    except Exception as e:
        print(f"Error saving product to waitlist: {e}")
        return "Unsuccessful"

async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    Retrieve user preferences.
    """
    try:
        preferences = await UserPreferences.read(user_id)
        return preferences.to_dict() if preferences else {}
    except Exception as e:
        print(f"Error fetching user preferences: {e}")
        return {}

async def get_product_specifications(product_id: str) -> Dict[str, Any]:
    """
    Retrieve detailed specifications for a product.
    """
    try:
        ecommerce_manager = get_ecommerce_manager()
        product = await ecommerce_manager.get_product_detail(product_id)
        return product if product else {}
    except Exception as e:
        print(f"Error fetching product specifications: {e}")
        return {}

async def track_product_price(
    user_id: str, product_id: str, targeted_price: float, current_price: float
) -> str:
    """
    Track a product's price for a user.
    """
    try:
        user = await get_user_by_id(user_id)
        if not user:
            return "Unsuccessful: User not found"

        ecommerce_manager = get_ecommerce_manager()
        product = await ecommerce_manager.get_product_detail(product_id)
        if product is None:
            try:
                product = await scraper.get_product_details(product_id)
            except Exception:
                return "Unsuccessful"
                
        product_data = ProductDetail.model_dump(product)
        await save_product(product_data, user)
        await TrackedItem.create(product_id, targeted_price, current_price, user.id)

        return "Successful"
    except Exception as e:
        print(f"Error tracking product price: {e}")
        return "Unsuccessful"
