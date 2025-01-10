from .chat.route import router as chat_router
from .auth.route import router as auth_router
from .product.route import router as product_router


__all__ = [
    "chat_router",
    "auth_router",
    "product_router",
]