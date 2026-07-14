from django.contrib import admin
from .models import CategorieCaveau, Caveau

@admin.register(CategorieCaveau)
class CategorieCaveauAdmin(admin.ModelAdmin):
    list_display = ('nom', 'largeur', 'longueur', 'prix_base')

@admin.register(Caveau)
class CaveauAdmin(admin.ModelAdmin):
    list_display = ('reference', 'statut', 'section', 'bloc', 'date_creation')
    list_filter = ('statut', 'section')
    search_fields = ('reference', 'section', 'bloc')