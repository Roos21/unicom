from django.db import models

from accounts.models import User
from core.timestamps import TimeStampedModel

class Category(TimeStampedModel):
    TYPE_CHOICES = [
        ('service', 'Service'),
        ('bien', 'Bien'),
    ]
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    is_validated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.type})"


class Product(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30, default="unité")  # ex : page, heure, feuille, copie
    is_active = models.BooleanField(default=True)
    is_validated = models.BooleanField(default=False)  # validation par admin

    def __str__(self):
        return self.name


class Sale(TimeStampedModel):
    PENDING = 'Pending'
    VALIDATED = 'Validated'
    REJECTED = 'Rejected'
    
    SALE_STATUS_CHOICES = [
        (PENDING, 'En attente de validation'),
        (VALIDATED, 'Validée'),
        (REJECTED, 'Rejetée'),
    ]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Référence au produit
    quantity = models.PositiveIntegerField()  # Quantité vendue
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Montant total de la vente
    last_total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)  # Date de la vente
    customer = models.CharField(max_length=255, null=True, blank=True)  # Nom ou informations du client
    payment_method = models.CharField(max_length=100, choices=[('Cash', 'Cash'), ('Credit', 'Credit')])  # Mode de paiement
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Utilisateur qui a créé la vente

    # Nouveau champ de statut
    status = models.CharField(
        max_length=10,
        choices=SALE_STATUS_CHOICES,
        default=VALIDATED
    )



    def __str__(self):
        return f"Vente de {self.product.name} pour {self.quantity} au client {self.customer}"

    def save(self, *args, **kwargs):
        self.total_price = self.product.price * self.quantity
        super().save(*args, **kwargs)