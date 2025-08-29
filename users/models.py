# users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

# Importez le modèle Boutique depuis l'application core
from core.models import Boutique

class User(AbstractUser):
    # Rôles des utilisateurs
    ROLE_ADMIN = 'admin'
    ROLE_SELLER = 'seller'
    USER_ROLES = [
        (ROLE_ADMIN, _('Admin principal')),
        (ROLE_SELLER, _('Vendeur')),
    ]

    role = models.CharField(
        max_length=10,
        choices=USER_ROLES,
        default=ROLE_SELLER,
        verbose_name=_("Rôle")
    )
    boutique = models.ForeignKey(
        Boutique,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_("Boutique assignée")
    )

 
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="custom_user_set", # <--- AJOUTEZ CETTE LIGNE
        related_query_name="custom_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_permissions_set", # <--- AJOUTEZ CETTE LIGNE
        related_query_name="custom_user_permission",
    )
    # FIN DES AJOUTS POUR RELATED_NAME

    class Meta:
        verbose_name = _("Utilisateur")
        verbose_name_plural = _("Utilisateurs")

    def __str__(self):
        return self.username

    @property
    def is_admin_principal(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_seller(self):
        return self.role == self.ROLE_SELLER