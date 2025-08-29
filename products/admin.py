from django.contrib import admin
from .models import Produit, Stock, MouvementStock # Importez vos modèles

# 1. Administration pour le modèle Produit
@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_code', 'price', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'product_code', 'description')
    date_hierarchy = 'created_at' # Permet une navigation par date

# 2. Administration pour le modèle Stock
@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'boutique', 'quantity', 'last_updated')
    list_filter = ('boutique', 'product')
    search_fields = ('product__name', 'boutique__name') # Permet de rechercher par nom de produit ou de boutique
    # Permet d'éditer la quantité directement depuis la liste (optionnel, à utiliser avec prudence)
    list_editable = ('quantity',)

# 3. Administration pour le modèle MouvementStock
@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('product', 'boutique', 'quantity', 'movement_type', 'user', 'timestamp')
    list_filter = ('movement_type', 'boutique', 'user', 'timestamp')
    search_fields = ('product__name', 'boutique__name', 'user__username', 'notes')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',) # Le champ timestamp est auto_now_add, donc non modifiable