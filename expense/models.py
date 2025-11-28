from django.db import models
from django.conf import settings



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

    def __str__(self):
        return f"{self.name} ({self.type})"


# ---------------------------------------------
# 2. CATEGORIE DE DEPENSES
# ---------------------------------------------
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


# ---------------------------------------------
# 3. SEUIL DE VALIDATION
# ---------------------------------------------
class ValidationThreshold(models.Model):
    min_amount = models.DecimalField(max_digits=12, decimal_places=2)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.PositiveIntegerField()  # niveau 1, 2, 3...

    def __str__(self):
        return f"Niveau {self.level} : {self.min_amount} - {self.max_amount}"


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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} - {self.amount} FCFA"


# ---------------------------------------------
# 6. APPROBATION MULTI-NIVEAUX
# ---------------------------------------------
class ApprovalStep(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name="approval_steps")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.PositiveIntegerField()  # dépend du seuil
    approved = models.BooleanField(default=False)
    rejected = models.BooleanField(default=False)
    comment = models.TextField(blank=True, null=True)
    validated_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Validation Niv {self.level} - {self.expense.title}"
