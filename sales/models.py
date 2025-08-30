# sales/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # Pour les timestamps précis

from users.models import User # Votre modèle User personnalisé
from core.models import Boutique # Le modèle Boutique
from products.models import Produit # Le modèle Produit

class Vente(models.Model):
    seller = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, # Si le vendeur est supprimé, la vente n'est pas supprimée, mais l'info du vendeur disparaît
        null=True,
        blank=True,
        related_name='sales',
        verbose_name=_("Vendeur")
    )
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE, # Si la boutique est supprimée, toutes ses ventes sont supprimées (logique, la vente s'est faite là)
        related_name='sales',
        verbose_name=_("Boutique")
    )
    sale_date = models.DateTimeField(default=timezone.now, verbose_name=_("Date de vente"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name=_("Montant total"))

    class Meta:
        verbose_name = _("Vente")
        verbose_name_plural = _("Ventes")
        ordering = ['-sale_date'] # Ordonne par date de vente la plus récente

    def __str__(self):
        return f"Vente #{self.id} par {self.seller.username if self.seller else 'N/A'} à {self.boutique.name} le {self.sale_date.strftime('%Y-%m-%d %H:%M')}"

    # Vous ajouterez ici des méthodes pour calculer le total, ajuster le stock, etc. plus tard


class LigneVente(models.Model):
    sale = models.ForeignKey(
        Vente,
        on_delete=models.CASCADE, # Si la vente est supprimée, les lignes de vente associées le sont aussi
        related_name='lignes_vente', # Permet d'accéder aux lignes depuis une vente (e.g., ma_vente.sale_items.all())
        verbose_name=_("Vente")
    )
    product = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE, # Si le produit est supprimé, la ligne de vente est aussi supprimée (car plus de référence produit)
        verbose_name=_("Produit")
    )
    quantity = models.PositiveIntegerField(verbose_name=_("Quantité"))
    price_at_sale = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Prix unitaire au moment de la vente"))

    class Meta:
        verbose_name = _("Ligne de Vente")
        verbose_name_plural = _("Lignes de Vente")
        unique_together = ('sale', 'product') # Un produit ne peut apparaître qu'une seule fois par vente

    def __str__(self):
        return f"{self.quantity} x {self.product.name} dans Vente #{self.sale.id}"

    # Méthode pour calculer le total de cette ligne
    @property
    def get_total_item_price(self):
        return self.quantity * self.price_at_sale
    
    @property
    def subtotal(self):
        """Calcule et retourne le sous-total pour cette ligne de vente."""
        return self.quantity * self.price_at_sale


class Facture(models.Model):
    sale = models.OneToOneField( # Une facture est liée à UNE SEULE vente, et une vente à UNE SEULE facture
        Vente,
        on_delete=models.CASCADE, # Si la vente est supprimée, la facture est aussi supprimée
        verbose_name=_("Vente associée")
    )
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name=_("Numéro de facture"))
    invoice_date = models.DateTimeField(default=timezone.now, verbose_name=_("Date d'émission"))
    # Chemin vers le fichier PDF généré
    pdf_file = models.FileField(upload_to='invoices/', blank=True, null=True, verbose_name=_("Fichier PDF"))

    class Meta:
        verbose_name = _("Facture")
        verbose_name_plural = _("Factures")
        ordering = ['-invoice_date']

    def __str__(self):
        return f"Facture #{self.invoice_number} pour Vente #{self.sale.id}"