from app.api.documents import router as documents_router
from app.api.chat import router as chat_router
from app.api.analytics import router as analytics_router

__all__ = ["documents_router", "chat_router", "analytics_router"]
