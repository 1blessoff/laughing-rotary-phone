from django.contrib import admin
from django.urls import path
from terrains.views_carte import carte_caveaux_view
from .api import api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),  # Swagger disponible à /api/docs
    path("carte-caveaux/", carte_caveaux_view) # pour la carte des caveaux
]



 