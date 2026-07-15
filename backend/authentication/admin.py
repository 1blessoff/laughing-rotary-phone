from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Champs affichés dans la liste des utilisateurs
    list_display = ('username', 'email', 'role', 'phone', 'is_active', 'is_staff')
    
    # Filtres dans la barre latérale
    list_filter = ('role', 'is_active', 'is_staff')
    
    # Champs de recherche
    search_fields = ('username', 'email', 'phone')
    
    # Ordre par défaut
    ordering = ('username',)
    
    # Configuration des champs pour la page d'édition
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'is_mfa_enabled'),
        }),
    )
    
    # Configuration des champs pour la page de création
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'is_mfa_enabled'),
        }),
    )