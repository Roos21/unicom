from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from expense.models import AccountMoney, Transaction
from .models import Credit, Sale


def _get_or_create_caisse_for_sale(sale):
    antenne = sale.created_by.antenne if sale.created_by else None
    defaults = {
        "name": f"Caisse {antenne.nom}" if antenne else "Caisse Principale",
        "balance": 0,
    }
    account, _ = AccountMoney.objects.get_or_create(
        type="CAISSE",
        antenne=antenne,
        defaults=defaults,
    )
    return account


@receiver(pre_save, sender=Sale)
def track_previous_sale_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return
    old = Sale.objects.filter(pk=instance.pk).only("status").first()
    instance._previous_status = old.status if old else None


@receiver(post_save, sender=Sale)
def automate_sale_cash_and_credit(sender, instance, created, **kwargs):
    # N'automatiser que les ventes validees
    if instance.status != Sale.VALIDATED:
        return

    if instance.payment_method == "Cash":
        if Transaction.objects.filter(sale=instance, type="IN").exists():
            return

        account = _get_or_create_caisse_for_sale(instance)
        Transaction.objects.create(
            account=account,
            type="IN",
            amount=instance.total_price,
            sale=instance,
        )
        return

    if instance.payment_method == "Credit":
        if getattr(instance, "credit", None):
            return

        customer_name = instance.customer or "Client credit"
        Credit.objects.create(
            nom=customer_name,
            telephone="N/A",
            date=instance.date or timezone.now(),
            sale=instance,
            status=Credit.PENDING,
        )


@receiver(pre_save, sender=Credit)
def track_previous_credit_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_status = None
        return
    old = Credit.objects.filter(pk=instance.pk).only("status").first()
    instance._previous_status = old.status if old else None


@receiver(post_save, sender=Credit)
def automate_credit_repayment(sender, instance, created, **kwargs):
    # Creer une entree de caisse uniquement au passage Pending -> Paid
    if created:
        return

    if instance.status != Credit.PAID:
        return

    previous = getattr(instance, "_previous_status", None)
    if previous == Credit.PAID:
        return

    sale = instance.sale
    if not sale:
        return

    if Transaction.objects.filter(sale=sale, type="IN").exists():
        return

    account = _get_or_create_caisse_for_sale(sale)
    Transaction.objects.create(
        account=account,
        type="IN",
        amount=sale.total_price,
        sale=sale,
    )
