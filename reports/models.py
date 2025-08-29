from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Boutique

User = get_user_model()

class Rapport(models.Model):
    TYPE_CHOICES = (
        ('daily', 'Journalier'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('annual', 'Annuel'),
    )

    type_rapport = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="Type de rapport")
    boutique = models.ForeignKey(Boutique, on_delete=models.CASCADE, related_name='reports', verbose_name="Boutique")
    date_debut = models.DateField(verbose_name="Date de début")
    date_fin = models.DateField(verbose_name="Date de fin")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Chiffre d'affaires total")
    num_sales = models.PositiveIntegerField(default=0, verbose_name="Nombre de ventes")
    generated_at = models.DateTimeField(default=timezone.now, verbose_name="Généré le")

    class Meta:
        verbose_name = "Rapport"
        verbose_name_plural = "Rapports"
        ordering = ['-generated_at']

    def __str__(self):
        return f"Rapport {self.get_type_rapport_display()} pour {self.boutique.name}"