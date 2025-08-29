from django.contrib import admin
from .models import Vente, LigneVente, Facture # Importez vos modèles


class LigneVenteInline(admin.TabularInline): # Ou admin.StackedInline pour une mise en page différente
    model = LigneVente
    extra = 1 # Affiche 1 ligne de vente vide par défaut pour l'ajout
    raw_id_fields = ('product',) # Utile pour rechercher des produits si vous en avez beaucoup

# 1. Administration pour le modèle Vente
@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'boutique', 'seller', 'sale_date', 'total_amount')
    list_filter = ('boutique', 'seller', 'sale_date')
    search_fields = ('id__exact', 'seller__username', 'boutique__name') # Recherche par ID de vente, nom de vendeur ou nom de boutique
    date_hierarchy = 'sale_date'
    inlines = [LigneVenteInline] # Associe l'inline pour que les lignes de vente apparaissent dans le formulaire de vente

    # Permet de calculer le total_amount automatiquement lors de l'enregistrement de la vente
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Recalcule le montant total de la vente après que les lignes de vente aient été sauvegardées
        obj.total_amount = sum(item.get_total_item_price for item in obj.sale_items.all())
        obj.save()


# 2. Administration pour le modèle Facture
@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'sale', 'invoice_date', 'pdf_file_link')
    list_filter = ('invoice_date',)
    search_fields = ('invoice_number', 'sale__id__exact')
    date_hierarchy = 'invoice_date'
    readonly_fields = ('invoice_date', 'pdf_file_link') # La date est auto, le lien est un champ calculé

    # Méthode pour afficher un lien vers le fichier PDF dans la liste de l'admin
    def pdf_file_link(self, obj):
        if obj.pdf_file:
            # Vous devrez ajuster l'URL en fonction de votre configuration des médias
            return f'<a href="{obj.pdf_file.url}" target="_blank">Voir PDF</a>'
        return "Pas de PDF"
    pdf_file_link.allow_tags = True
    pdf_file_link.short_description = "Fichier PDF"