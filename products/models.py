from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings # <-- NOUVEL IMPORT

# Importez les modèles nécessaires des autres applications
from core.models import Boutique
# from users.models import User # <-- SUPPRIMEZ OU COMMENTEZ CETTE LIGNE !

class Produit(models.Model):
    name = models.CharField(max_length=200, verbose_name=_("Nom du produit"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Prix unitaire"))
    product_code = models.CharField(max_length=50, unique=True, verbose_name=_("Code produit"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Date de dernière modification"))

    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.product_code})"


class Stock(models.Model):
    product = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_("Produit")
    )
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name=_("Boutique")
    )
    quantity = models.IntegerField(default=0, verbose_name=_("Quantité"))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_("Dernière mise à jour"))

    class Meta:
        verbose_name = _("Stock")
        verbose_name_plural = _("Stocks")
        unique_together = ('product', 'boutique')

    def __str__(self):
        return f"{self.product.name} - {self.boutique.name}: {self.quantity}"


class MouvementStock(models.Model):
    MOVEMENT_TYPES = [
        ('entry', _('Entrée')),
        ('exit', _('Sortie')),
        ('transfer', _('Transfert')),
    ]

    product = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_("Produit")
    )
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE,
        related_name='stock_movements',
        verbose_name=_("Boutique")
    )
    quantity = models.IntegerField(verbose_name=_("Quantité"))
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES, verbose_name=_("Type de mouvement"))
    
    # L'utilisateur qui a effectué le mouvement
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # <-- C'EST LA CORRECTION CLÉ ICI !
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_("Effectué par")
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name=_("Date et heure du mouvement"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    class Meta:
        verbose_name = _("Mouvement de Stock")
        verbose_name_plural = _("Mouvements de Stock")
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.movement_type} de {self.quantity} x {self.product.name} à {self.boutique.name}"