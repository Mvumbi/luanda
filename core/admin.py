from django.contrib import admin
from .models import Boutique

@admin.register(Boutique)
class BoutiqueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_main')
    list_filter = ('is_main', 'city')
    ordering = ('name',)
    search_fields = ('name', 'address')