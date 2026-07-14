from ninja import NinjaAPI
from authentication.views import auth_router
from terrains.api import router as terrains_router
from reservations.api import router as reservations_router
from concessions.api import router as concessions_router
from finances.api_paiements import router as finances_router
from audit.api import router as audit_router


api = NinjaAPI(title="Gestion Funéraire API", version="1.0.0")

# Routers
api.add_router("/auth", auth_router)
api.add_router("/caveaux", terrains_router)
api.add_router("/reservations", reservations_router)
api.add_router("/concessions", concessions_router)
api.add_router("/paiements", finances_router)
api.add_router("/audit", audit_router)


@api.get("/hello")
def hello(request):
    return {"message": "Bienvenue sur l'API de Gestion Funéraire"}

@api.get("/ping")
def ping(request):
    return {"status": "ok", "message": "API fonctionnelle"}