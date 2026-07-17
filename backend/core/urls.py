# backend/core/urls.py
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from terrains.views_carte import carte_caveaux_view
from .api import api  # API Ninja principale

def home_view(request):
    return JsonResponse({
        'message': 'Bienvenue sur Gestion Funéraire API',
        'status': 'online',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'api': '/api/',
            'docs': '/api/docs',
            'auth': '/api/auth',
            'caveaux': '/api/caveaux',
            'reservations': '/api/reservations',
            'concessions': '/api/concessions',
            'paiements': '/api/paiements',
            'audit': '/api/audit',
            'carte_caveaux': '/carte-caveaux/',
        }
    })

urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    
    # TOUTES les routes API via Ninja
    path('api/', api.urls),  # Cela inclut /api/auth, /api/caveaux, etc.
    
    # Autres routes (non-API)
    path("carte-caveaux/", carte_caveaux_view),
]