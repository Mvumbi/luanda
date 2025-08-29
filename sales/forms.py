from django import forms
from .models import Vente, LigneVente # Importe tes modèles de vente
from products.models import Produit # Importe le modèle Produit
from core.models import Boutique # Assure-toi que ce chemin est correct pour ton modèle Boutique

class VenteForm(forms.ModelForm):
    class Meta:
        model = Vente
        # Le champ 'notes' a été retiré, car il n'est pas dans ton modèle Vente
        fields = ['boutique'] 
        widgets = {
            'boutique': forms.Select(attrs={'class': 'form-control'}), 
        }
        labels = {
            'boutique': "Boutique",
        }

class LigneVenteForm(forms.ModelForm):
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
                'readonly': 'readonly'
            }),
        }
        labels = {
            'product': "Produit",
            'quantity': "Quantité",
            'price_at_sale': "Prix unitaire (au moment de la vente)",
        }