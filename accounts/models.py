from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings

from core.models.mixins import SoftDeleteMixin


class User(AbstractUser, PermissionsMixin, SoftDeleteMixin):
    """
    Modèle utilisateur personnalisé pour la plateforme de gestion de cybercafés.
    Contient :
    - Gestion des rôles
    - Suivi des connexions
    - Soft Delete avec trace (deleted_by)
    """

    # RÔLES DU SYSTÈME
    class Role(models.TextChoices):
        GERANT = "gerant", "Gérant d'antenne"
        ADMIN = "admin", "Admin central"
        DIRECTEUR = "directeur", "Directeur"
        SUPERVISEUR = "superviseur", "Superviseur régional"

    # ROLE PAR DÉFAUT
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.GERANT,
        help_text="Détermine les permissions et les accès aux modules."
    )

    # INFORMATIONS ANTENNE
    antenne = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Nom de l'antenne rattachée"
    )

    # CONTACT PROFESSIONNEL
    telephone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numéro de téléphone professionnel"
    )

    # STATUTS DU COMPTE
    is_blocked = models.BooleanField(
        default=False,
        help_text="Blocage manuel : coupe l'accès sans supprimer le compte."
    )

    # META INFOS
    date_creation = models.DateTimeField(
        auto_now_add=True,
        help_text="Date de création du compte"
    )

    date_derniere_connexion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Dernière connexion réussie"
    )
    # Ajoute ces lignes dans ton modèle User, juste après les champs personnalisés
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='accounts_user_set',
        related_query_name='accounts_user',
        blank=True,
        help_text='Groupes de permissions de l’utilisateur.'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='accounts_user_set',
        related_query_name='accounts_user',
        blank=True,
        help_text='Permissions spécifiques de l’utilisateur.'
    )
    # CONNEXION

    def enregistrer_connexion(self):
        """Met à jour la dernière connexion"""
        self.date_derniere_connexion = timezone.now()
        self.save(update_fields=["date_derniere_connexion"])

    # HELPERS ROLES
    def est_gerant(self): return self.role == self.Role.GERANT
    def est_admin(self): return self.role == self.Role.ADMIN
    def est_directeur(self): return self.role == self.Role.DIRECTEUR
    def est_superviseur(self): return self.role == self.Role.SUPERVISEUR

    # REPRÉSENTATION
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def has_permission(self, permission_name):
        from .permissions import ROLE_PERMISSIONS
        return permission_name in ROLE_PERMISSIONS.get(self.role, set())
    
class Ville(models.Model):
    """Model definition for Ville."""
    name = models.CharField(max_length = 150)
    

    class Meta:
        """Meta definition for Ville."""

        verbose_name = 'Ville'
        verbose_name_plural = 'Villes'

    def __str__(self):
        """Unicode representation of Ville."""
        return self.name

class Antenne(models.Model):
    """Model definition for Antenne."""
    nom = models.CharField(max_length = 150, null=True, blank=True)
    lieux = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)
    gerant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gerant')

    class Meta:
        """Meta definition for Antenne."""

        verbose_name = 'Antenne'
        verbose_name_plural = 'Antennes'

    def __str__(self):
        """Unicode representation of Antenne."""
        return f'{self.nom}'




