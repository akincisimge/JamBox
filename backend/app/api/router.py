from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.kelime_kapismasi import router as kelime_kapismasi_router
from app.api.routes.papaz_kacti import router as papaz_kacti_router
from app.api.routes.pisti import router as pisti_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.tek_kart import router as tek_kart_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(users_router, tags=["users"])
api_router.include_router(rooms_router, tags=["rooms"])
api_router.include_router(pisti_router, tags=["pisti"])
api_router.include_router(papaz_kacti_router, tags=["papaz-kacti"])
api_router.include_router(tek_kart_router, tags=["tek-kart"])
api_router.include_router(kelime_kapismasi_router, tags=["kelime-kapismasi"])
