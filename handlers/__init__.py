from .start import router as start_router
from .ai_handler import router as ai_router
from .natal import router as natal_router
from .admin_simple import router as admin_router
from .horoscope import router as horoscope_router
from .compatibility import router as compatibility_router
from .profile import router as profile_router
from .pdf_handler import router as pdf_router
from .payment import router as payment_router

from .menu_commands import router as menu_router
from .mood_diary import router as mood_router
from .admin_ads import router as ads_router
__all__ = [
    "start_router",
    "ai_router",
    "natal_router",
    "admin_router",
    "horoscope_router",
    "compatibility_router",
    "profile_router",
    "pdf_router",
    "payment_router",
    'menu_router',
    'mood_router',
    'ads_router',
]
