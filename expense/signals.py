from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Expense, Transaction, ApprovalStep, AccountMoney, ValidationThreshold

# ------------------------------
# SIGNAL 1 : Gestion du solde sur Transaction
# ------------------------------
@receiver(post_save, sender=Transaction)
def update_account_balance_on_transaction(sender, instance, created, **kwargs):
    """
    Met à jour le solde du compte associé lors de la création d'une transaction.
    IN -> augmente le solde
    OUT -> diminue le solde
    """
    if not created:
        return  # On ne fait rien si la transaction est modifiée

    account = instance.account

    if instance.type == "IN":
        account.balance += instance.amount
    elif instance.type == "OUT":
        if account.balance < instance.amount:
            instance.delete()
            
            raise ValidationError(f"Solde insuffisant dans le compte {account.name}")
        
        account.balance -= instance.amount

    account.save(update_fields=["balance"])

# ------------------------------
# SIGNAL 2 : Création d'étapes d'approbation pour une dépense
# ------------------------------
@receiver(post_save, sender=Expense)
def create_approval_steps(sender, instance, created, **kwargs):
    if not created:
        return

    # Chercher les seuils correspondant
    thresholds = ValidationThreshold.objects.filter(
        min_amount__lte=instance.amount,
        max_amount__gte=instance.amount
    ).order_by("level")

    # Créer les étapes de validation
    for t in thresholds:
        ApprovalStep.objects.create(
            expense=instance,
            level=t.level,
            role=t.role,
            approved=False,
            rejected=False
        )

    # Si aucun seuil, auto-approbation
    if not thresholds.exists():
        instance.status = "APPROVED"
    else:
        instance.status = "IN_REVIEW"
    instance.save(update_fields=["status"])

# ------------------------------
# SIGNAL 3 : Créer transaction OUT après approbation de toutes les étapes
# ------------------------------
@receiver(post_save, sender=ApprovalStep)
def create_transaction_when_expense_approved(sender, instance, **kwargs):
    expense = instance.expense
    steps = expense.steps.all()

    # Si une étape est rejetée → statut REJECTED
    if steps.filter(rejected=True).exists():
        expense.status = "REJECTED"
        expense.save(update_fields=["status"])
        return

    # Si toutes les étapes sont approuvées
    if steps.filter(approved=True).count() == steps.count():
        # Si le statut n'est pas déjà APPROVED
        if expense.status != "APPROVED":
            expense.status = "APPROVED"
            expense.save(update_fields=["status"])

        # Vérifier qu'aucune transaction OUT n'existe pour cette dépense
        if not Transaction.objects.filter(expense=expense, type="OUT").exists():
            account = expense.account

            # Vérifier solde suffisant
            if account.balance < expense.amount:
                # Lever erreur ici, le signal ne peut pas faire de message HTTP
                raise ValidationError(
                    f"Solde insuffisant dans le compte {account.name} pour la dépense {expense.title}"
                )

            # Créer transaction OUT
            Transaction.objects.create(
                account=account,
                type="OUT",
                amount=expense.amount,
                expense=expense
            )

# ------------------------------
# SIGNAL 4 : Créer transaction OUT quand la dépense passe en PAYÉ
# ------------------------------
""" @receiver(pre_save, sender=Expense)
def create_transaction_when_expense_paid(sender, instance, **kwargs):
    if not instance.pk:
        return  # Nouvelle dépense, on ignore

    previous = Expense.objects.get(pk=instance.pk)

    if previous.status != "PAID" and instance.status == "PAID":
        account = instance.account

        # Vérifier solde suffisant
        if account.balance < instance.amount:
            raise ValidationError(f"Solde insuffisant dans le compte {account.name}")

        # Créer transaction OUT si elle n'existe pas
        exists = Transaction.objects.filter(expense=instance, type="OUT").exists()
        if not exists:
            Transaction.objects.create(
                account=account,
                type="OUT",
                amount=instance.amount,
                expense=instance
            )
 """