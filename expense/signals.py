from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from .models import ApprovalStep, Transaction, Expense, AccountMoney, ValidationThreshold
from decimal import Decimal


# ------------------------------------------------
# SIGNAL 1 : Mise à jour du compte après transaction
# ------------------------------------------------
@receiver(pre_save, sender=Transaction)
def update_account_on_transaction_update(sender, instance, **kwargs):
    """
    Si une transaction existe déjà, on enlève son effet du solde
    avant d'appliquer le nouveau montant.
    """
    if instance.pk:
        old_tr = Transaction.objects.get(pk=instance.pk)

        # reverser l'ancien effet
        if old_tr.type == "IN":
            instance.account.balance -= old_tr.amount
        else:
            instance.account.balance += old_tr.amount


@receiver(post_save, sender=Transaction)
def update_account_on_transaction_save(sender, instance, created, **kwargs):
    """
    Applique l'effet de la transaction sur le solde.
    """
    account = instance.account

    if instance.type == "IN":
        account.balance += instance.amount
    else:
        account.balance -= instance.amount

    account.save()


@receiver(post_save, sender=Expense)
def create_transaction_when_expense_paid(sender, instance, **kwargs):
    """
    Si une dépense passe en statut PAYÉ → on crée une transaction sortante.
    """
    if instance.status == "PAID":

        # empêcher les doublons
        exists = Transaction.objects.filter(expense=instance).exists()
        if exists:
            return

        Transaction.objects.create(
            account=instance.account,
            type="OUT",
            amount=instance.amount,
            expense=instance,
        )

@receiver(post_save, sender=Expense)
def create_approval_steps(sender, instance, created, **kwargs):
    if not created:
        return

    amount = instance.amount

    # Chercher les seuils correspondant
    thresholds = ValidationThreshold.objects.filter(
        min_amount__lte=amount,
        max_amount__gte=amount
    ).order_by("level")

    # Créer les étapes de validation
    for t in thresholds:
        ApprovalStep.objects.create(
            expense=instance,
            approver=t.approver,
            level=t.level
        )

    # Si aucun seuil → auto-approval ?
    if not thresholds.exists():
        instance.status = "APPROVED"
        instance.save()
    else:
        instance.status = "IN_REVIEW"
        instance.save()


@receiver(post_save, sender=ApprovalStep)
def update_expense_status(sender, instance, **kwargs):
    expense = instance.expense
    steps = expense.approval_steps.all()

    # Si une étape est rejetée → rejet global
    if steps.filter(rejected=True).exists():
        expense.status = "REJECTED"
        expense.save()
        return

    # Si toutes les étapes sont validées
    if steps.filter(approved=True).count() == steps.count():
        expense.status = "APPROVED"
        expense.save()


@receiver(pre_save, sender=Expense)
def process_payment(sender, instance, **kwargs):
    if not instance.pk:
        return  # dépense nouvellement créée, on ignore

    previous = Expense.objects.get(pk=instance.pk)

    # Vérifier changement de statut vers PAYÉ
    if previous.status != "PAID" and instance.status == "PAID":
        account = instance.account

        # Empêcher le solde négatif
        if account.balance < instance.amount:
            raise ValidationError("Solde insuffisant dans le compte !")

        # Débiter le compte
        account.balance -= instance.amount
        account.save()

        # Créer une transaction de sortie
        Transaction.objects.create(
            account=account,
            type="OUT",
            amount=instance.amount,
            expense=instance
        )


@receiver(post_save, sender=Transaction)
def update_account_balance(sender, instance, created, **kwargs):
    if not created:
        return
    
    account = instance.account

    if instance.type == "IN":
        account.balance += instance.amount
    else:
        # éviter solde négatif
        if account.balance < instance.amount:
            raise ValidationError("Impossible : solde insuffisant.")
        account.balance -= instance.amount

    account.save()
