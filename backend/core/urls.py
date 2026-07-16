from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from terrains.views_carte import carte_caveaux_view
from .api import api

# Vue pour la page d'accueil
def home_view(request):
    return JsonResponse({
        'message': 'Bienvenue sur Gestion Funéraire API',
        'status': 'online',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'api_docs': '/api/docs',
            'carte_caveaux': '/carte-caveaux/',
        }
    })

urlpatterns = [
    path('', home_view, name='home'),  # AJOUT DE CETTE LIGNE
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # Swagger disponible à /api/docs
    path("carte-caveaux/", carte_caveaux_view),  # pour la carte des caveaux
]