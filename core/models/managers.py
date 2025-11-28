# core/models/managers.py

from django.db import models

class SoftDeleteManager(models.Manager):
    """Manager qui retourne uniquement les objets non supprimés."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteAllManager(models.Manager):
    """Manager qui retourne absolument tout, même supprimé."""
    def get_queryset(self):
        return super().get_queryset()
