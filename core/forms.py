# core/forms.py

from django import forms
from .models import Boutique
from django.utils.translation import gettext_lazy as _

class BoutiqueForm(forms.ModelForm):
    class Meta:
        model = Boutique
        # Inclure tous les champs que tu souhaites gérer via le formulaire
        # 'name', 'address', 'city', 'is_main'
        fields = ['name', 'address', 'city', 'is_main']
        
        # Les labels et help_texts sont automatiquement pris des verbose_name de ton modèle
        # mais tu peux les surcharger ici si tu veux des textes différents pour le formulaire.
        # Dans ce cas, les verbose_name de ton modèle sont déjà bons,
        # donc on peut les laisser faire leur travail par défaut ou les réaffirmer.
        labels = {
            'name': _("Nom de la boutique"),
            'address': _("Adresse"),
            'city': _("Ville"),
            'is_main': _("Boutique principale"),
        }
        
        help_texts = {
            'address': _("Adresse complète de la boutique."),
            'city': _("La ville où se situe la boutique (par défaut : Luanda)."),
            'is_main': _("Cochez si c'est la boutique principale. Une seule boutique peut être principale."),
        }
        
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}), # Un champ texte plus grand pour l'adresse
            # Tu pourrais ajouter d'autres widgets pour 'city' ou 'is_main' si besoin
        }