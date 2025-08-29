from django.db import models
from django.utils.translation import gettext_lazy as _

class Boutique(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Nom de la boutique"))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Adresse"))
    city = models.CharField(max_length=100, default='Luanda', verbose_name=_("Ville"))
    is_main = models.BooleanField(default=False, verbose_name=_("Boutique principale"))

    class Meta:
        verbose_name = _("Boutique")
        verbose_name_plural = _("Boutiques")
        constraints = [
            models.UniqueConstraint(fields=['is_main'], condition=models.Q(is_main=True), name='unique_main_boutique')
        ]


    def __str__(self):
        return self.name