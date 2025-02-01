from .chat.route import router as chat_router
from .auth.route import router as auth_router
from .product.route import router as product_router, queue_worker
from .track.route import router as track_router
from .payments.route import router as payment_router


__all__ = [
    "chat_router",
    "auth_router",
    "product_router",
    "track_router",
    "queue_worker",
    "payment_router",
]