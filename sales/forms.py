from django import forms
from .models import Vente, LigneVente
from products.models import Produit
from core.models import Boutique

class VenteForm(forms.ModelForm):
    """
    Formulaire pour la création et la mise à jour du modèle Vente.
    """
    class Meta:
        model = Vente
        # Le champ 'seller' est omis car il sera automatiquement défini par la vue (request.user)
        # Le champ 'sale_date' est géré par la valeur par défaut du modèle
        # Le champ 'total_amount' est calculé et mis à jour dans la vue
        fields = ['boutique'] 
        widgets = {
            'boutique': forms.Select(attrs={'class': 'form-control'}), 
        }
        labels = {
            'boutique': "Boutique",
        }

class LigneVenteForm(forms.ModelForm):
    """
    Formulaire pour la création et la mise à jour du modèle LigneVente.
    Ce formulaire est destiné à être utilisé dans un formset.
    """
    # Ce champ est nécessaire pour la sélection du produit dans le formset
    product = forms.ModelChoiceField(
        queryset=Produit.objects.all().order_by('name'),
        label="Produit",
        empty_label="Sélectionner un produit",
        widget=forms.Select(attrs={'class': 'form-select'}) 
    )

    class Meta:
        model = LigneVente
        fields = ['product', 'quantity', 'price_at_sale']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1, 'placeholder': 'Quantité', 'class': 'form-control'}),
            'price_at_sale': forms.NumberInput(attrs={
                'step': '0.01', 
                'placeholder': 'Prix unitaire',
                'class': 'form-control',
                'readonly': 'readonly'  # Le prix est affiché mais non modifiable par l'utilisateur
            }),
        }
        labels = {
            'product': "Produit",
            'quantity': "Quantité",
            'price_at_sale': "Prix unitaire (au moment de la vente)",
        }