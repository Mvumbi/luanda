from django.contrib import admin
from django.contrib.auth.admin import UserAdmin # Importez UserAdmin pour étendre l'admin par défaut
from .models import User # Importez votre modèle User personnalisé

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Permet d'ajouter vos champs personnalisés (role, boutique) aux formulaires de création/modification d'utilisateur
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'boutique')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'boutique')}),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'boutique')
    # Permet de filtrer les utilisateurs par ces champs
    list_filter = ('role', 'boutique', 'is_staff', 'is_superuser', 'is_active')