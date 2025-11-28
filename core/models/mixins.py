# core/models/mixins.py

from django.db import models
from django.utils import timezone
from django.conf import settings

class SoftDeleteMixin(models.Model):
    """
    Mixin pour soft delete avec trace :
    - is_deleted
    - deleted_at
    - deleted_by : utilisateur qui a supprimé
    """

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_%(class)ss"
    )

    class Meta:
        abstract = True

    def delete(self, user=None, using=None, keep_parents=False):
        """
        Soft delete :
        - user : l'utilisateur qui supprime
        - stocke la date et l'auteur
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()

        if user:
            self.deleted_by = user

        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self):
        """Restaure un objet supprimé"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])
