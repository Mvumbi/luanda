from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

# Importez le modèle Boutique de l'application core
from core.models import Boutique

class RapportMensuel(models.Model):
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.CASCADE, # Si la boutique est supprimée, ses rapports mensuels le sont aussi
        related_name='monthly_reports',
        verbose_name=_("Boutique")
    )
    month = models.PositiveIntegerField(verbose_name=_("Mois"))
    year = models.PositiveIntegerField(verbose_name=_("Année"))
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name=_("Chiffre d'affaires total"))
    num_sales = models.PositiveIntegerField(default=0, verbose_name=_("Nombre de ventes"))
    top_selling_products = models.JSONField(blank=True, null=True, verbose_name=_("Produits les plus vendus")) # Stockera une liste de dictionnaires
    low_stock_alerts = models.JSONField(blank=True, null=True, verbose_name=_("Alertes stock bas")) # Stockera une liste de dictionnaires
    generated_at = models.DateTimeField(default=timezone.now, verbose_name=_("Généré le"))
    # Chemin vers le fichier PDF ou Excel du rapport
    report_file = models.FileField(upload_to='monthly_reports/', blank=True, null=True, verbose_name=_("Fichier du rapport"))

    class Meta:
        verbose_name = _("Rapport Mensuel")
        verbose_name_plural = _("Rapports Mensuels")
        unique_together = ('boutique', 'month', 'year') # Un seul rapport par boutique par mois/année
        ordering = ['-year', '-month'] # Ordonne par année puis par mois (du plus récent au plus ancien)

    def __str__(self):
        return f"Rapport de {self.boutique.name} - {self.month}/{self.year}"