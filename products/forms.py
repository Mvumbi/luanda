# products/forms.py

from django import forms
from .models import Produit, Stock, MouvementStock
from core.models import Boutique
from django.utils.translation import gettext_lazy as _

class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = ['name', 'description', 'price', 'product_code']
        labels = {
            'name': _("Nom du produit"),
            'description': _("Description du produit"),
            'price': _("Prix unitaire"),
            'product_code': _("Code produit unique"),
        }
        help_texts = {
            'product_code': _("Code unique pour identifier le produit (ex: SKU, code-barres)."),
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


# Nouveau formulaire pour la gestion des Stocks
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'boutique', 'quantity']
        labels = {
            'product': _("Produit"),
            'boutique': _("Boutique"),
            'quantity': _("Quantité en stock"),
        }
        help_texts = {
            'quantity': _("Quantité actuelle de ce produit dans cette boutique."),
        }
    
    # Pour personnaliser les listes déroulantes (optionnel, mais recommandé)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Permet de trier les produits et boutiques dans les listes déroulantes
        self.fields['product'].queryset = Produit.objects.all().order_by('name')
        self.fields['boutique'].queryset = Boutique.objects.all().order_by('name')


# Nouveau formulaire pour les Mouvements de Stock
class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['product', 'boutique', 'quantity', 'movement_type', 'notes']
        labels = {
            'product': _("Produit"),
            'boutique': _("Boutique"),
            'quantity': _("Quantité déplacée"),
            'movement_type': _("Type de mouvement"),
            'notes': _("Notes (optionnel)"),
        }
        help_texts = {
            'quantity': _("Quantité à ajouter (entrée) ou à retirer (sortie)."),
            'movement_type': _("Sélectionnez le type d'opération (entrée, sortie, transfert)."),
            'notes': _("Informations supplémentaires sur ce mouvement (ex: raison de la sortie, fournisseur)."),
        }
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    # Validation personnalisée pour s'assurer qu'une sortie ne dépasse pas le stock disponible
    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        boutique = cleaned_data.get('boutique')
        quantity = cleaned_data.get('quantity')
        movement_type = cleaned_data.get('movement_type')

        if movement_type == 'exit' and product and boutique:
            try:
                # Récupère le stock actuel pour ce produit et cette boutique
                current_stock = Stock.objects.get(product=product, boutique=boutique).quantity
            except Stock.DoesNotExist:
                current_stock = 0

            if quantity > current_stock:
                raise forms.ValidationError(
                    _("La quantité de sortie ({}) est supérieure au stock disponible ({}).").format(quantity, current_stock)
                )
        elif movement_type == 'entry' and quantity is not None and quantity < 0:
            raise forms.ValidationError(
                _("La quantité d'entrée ne peut pas être négative.")
            )
        
        # Pour les transferts, tu pourrais ajouter une logique plus complexe ici,
        # comme spécifier une boutique de destination et valider les stocks des deux côtés.
        # Pour l'instant, on se concentre sur les sorties/entrées.

        return cleaned_data