from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from expense.models import AccountMoney, Expense, Transaction
from .models import Sale


# -----------------------------
# SIGNAL POUR LES VENTES
# -----------------------------
@receiver(post_save, sender=Sale)
def update_account_on_sale(sender, instance, created, **kwargs):
    """
    Lorsqu'une vente est validée, on crédite le compte de la caisse.
    """
    if not created:
        return  # On ne traite que les nouvelles ventes

    # Choisir le compte à créditer, ici la caisse
    account = AccountMoney.objects.get(type="CAISSE")
    if not account:
        raise ValidationError("Aucun compte de type CAISSE trouvé pour enregistrer la vente.")

    # Créer une transaction IN pour la vente
    Transaction.objects.create(
        account=account,
        type="IN",
        amount=instance.total_price,
        sale=instance
    )

    # Mettre à jour le solde
    account.balance += instance.total_price
    account.save()


