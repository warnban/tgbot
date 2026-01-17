from aiogram import Router

from .start import router as start_router
from .profile import router as profile_router
from .calculator import router as calculator_router
from .resorts import router as resorts_router
from .buddy_search import router as buddy_router
from .events import router as events_router
from .contacts import router as contacts_router
from .instructors import router as instructors_router
from .sos import router as sos_router
from .reviews import router as reviews_router
from .chat import router as chat_router
from .admin import router as admin_router
from .fallback import router as fallback_router


def setup_routers() -> Router:
    """Собирает все роутеры в один."""
    router = Router()
    
    # Порядок важен — admin и start первыми, fallback последним!
    router.include_router(admin_router)
    router.include_router(start_router)
    router.include_router(profile_router)
    router.include_router(calculator_router)
    router.include_router(resorts_router)
    router.include_router(buddy_router)
    router.include_router(events_router)
    router.include_router(contacts_router)
    router.include_router(instructors_router)
    router.include_router(sos_router)
    router.include_router(reviews_router)
    router.include_router(chat_router)
    # Fallback должен быть ПОСЛЕДНИМ — он ловит всё остальное
    router.include_router(fallback_router)
    
    return router
