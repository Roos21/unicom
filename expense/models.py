from django.db import models
from django.conf import settings

from accounts.models import User
from sales.models import Sale



# ---------------------------------------------
# 1. COMPTE : caisse ou compte bancaire
# ---------------------------------------------
class AccountMoney(models.Model):
    ACCOUNT_TYPES = (
        ("CAISSE", "Caisse"),
        ("BANQUE", "Compte Bancaire"),
    )

    name = models.CharField(max_length=150)
    type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)  

    def __str__(self):
        return f"{self.name} ({self.type})"


# ---------------------------------------------
# 2. CATEGORIE DE DEPENSES
# ---------------------------------------------
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)  

    def __str__(self):
        return self.name


# ---------------------------------------------
# 3. SEUIL DE VALIDATION
# ---------------------------------------------
class ValidationThreshold(models.Model):
    level = models.PositiveIntegerField()
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    role = models.CharField(max_length=50, choices=User.Role.choices)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)  

    def __str__(self):
        return f"Niveau {self.level} : {self.min_amount} - {self.max_amount or '∞'}"


# ---------------------------------------------
# 4. DEPENSE
# ---------------------------------------------
class Expense(models.Model):
    STATUS = (
        ("PENDING", "En attente"),
        ("IN_REVIEW", "En validation"),
        ("APPROVED", "Approuvée"),
        ("REJECTED", "Rejetée"),
        ("PAID", "Payée"),
    )

    title = models.CharField(max_length=255)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True)
    account = models.ForeignKey(AccountMoney, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses_created")
    status = models.CharField(max_length=20, choices=STATUS, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.amount} FCFA"


# ---------------------------------------------
# 5. TRANSACTION (entrée/sortie dans les comptes)
# ---------------------------------------------
class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ("IN", "Entrée"),
        ("OUT", "Sortie"),
    )

    account = models.ForeignKey(AccountMoney, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense = models.ForeignKey(Expense, on_delete=models.SET_NULL, null=True, blank=True)
    sale = models.ForeignKey(Sale, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} FCFA"


# ---------------------------------------------
# 6. APPROBATION MULTI-NIVEAUX
# ---------------------------------------------
class ApprovalStep(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="steps")
    level = models.PositiveIntegerField()
    role = models.CharField(max_length=20, choices=User.Role.choices)

    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)

    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)  

    def __str__(self):
        return f"Dépense {self.expense.id} — Niveau {self.level} ({self.role})"
