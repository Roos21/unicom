from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from expense.models import AccountMoney, Expense, Transaction
from .models import Credit, Sale


# -----------------------------
# SIGNAL POUR LES VENTES
# -----------------------------
@receiver(post_save, sender=Sale)
def update_account_on_sale(sender, instance, created, **kwargs):
    """
    Gère la création d'une Transaction (Cash) ou d'une Créance (Crédit) 
    lorsqu'une nouvelle vente est validée.
    """
    
    # 1. On traite uniquement les nouvelles ventes
    # Note: Dans un système réel, il est souvent préférable de vérifier 
    # le statut (instance.status == Sale.VALIDATED) également.
    if not created:
        return 

    # --- Logique conditionnelle basée sur le mode de paiement ---

    if instance.payment_method == 'Cash':
        
        ## A. GESTION DU PAIEMENT CASH
        
        # 1. Choisir le compte à créditer (la caisse)
        try:
            # Idéalement, utilisez un ID ou une configuration plus robuste que le type en dur
            account = AccountMoney.objects.get(type="CAISSE")
        except AccountMoney.DoesNotExist:
            # Gérer l'exception si le compte CAISSE n'existe pas
            print("Erreur: Aucun compte de type CAISSE trouvé.")
            return # Ou raise ValidationError("...")

        # 2. Créer une transaction IN (Entrée) pour le mouvement de caisse
        Transaction.objects.create(
            account=account,
            type="IN",
            amount=instance.total_price,
            sale=instance
        )
        
    elif instance.payment_method == 'Credit':
        
        ## B. GESTION DU PAIEMENT CRÉDIT (Créance Client)

        # 1. Vérification des informations client (à adapter selon vos besoins)
        customer_name = instance.customer.split(',')[0] if instance.customer else "Client Inconnu"
        # Il vous manque le champ téléphone dans votre modèle Sale. 
        # Si vous n'avez pas le téléphone dans Sale, utilisez une valeur par défaut.
        customer_phone = instance.customer.split(',')[1] if instance.customer else "N/A" 
        
        # 2. Créer une instance de Créance (Credit)
        Credit.objects.create(
            nom=customer_name,
            telephone=customer_phone,
            # La date de la créance est la date de la vente
            date=instance.date, 
            sale=instance
            # Le statut par défaut est 'Pending'
            # Note: Votre modèle Credit est incomplet, il manque le montant total dû !
        )
        
        # NOTE IMPORTANTE: 
        # Le solde du compte (AccountMoney) n'est PAS mis à jour ici car l'argent n'est pas reçu.
        
    else:
        # Gérer les autres modes de paiement si nécessaire (par exemple, "BANQUE")
        pass


@receiver(post_save, sender=Sale)
def update_account_on_sale(sender, instance, created, **kwargs):
    """
    Gère la création d'une Transaction liée à la caisse DE L'ANTENNE 
    ou d'une Créance (Crédit) lorsqu'une nouvelle vente est validée.
    """
    if not created:
        return 

    # 1. Identifier l'antenne du vendeur (créateur de la vente)
    vendeur = instance.created_by
    if not vendeur or not hasattr(vendeur, 'antenne'): # Remplacez par le nom de votre champ FK
        # Optionnel: lever une erreur si le vendeur n'est pas rattaché à une antenne
        return

    antenne_du_vendeur = vendeur.antenne

    # --- Logique basée sur le mode de paiement ---

    if instance.payment_method == 'Cash':
        
        ## A. GESTION DU PAIEMENT CASH PAR ANTENNE
        
        # On cherche la CAISSE spécifiquement liée à cette ANTENNE
        account = AccountMoney.objects.filter(
            antenne=antenne_du_vendeur, 
            type="CAISSE"
        ).first()

        if not account:
            # Sécurité : On ne peut pas valider une vente cash sans caisse configurée pour l'antenne
            raise ValidationError(f"Configuration manquante : Aucune caisse trouvée pour l'antenne {antenne_du_vendeur.nom}")

        # Création de la transaction dans la bonne caisse
        Transaction.objects.create(
            account=account,
            type="IN",
            amount=instance.total_price,
            sale=instance
        )
        
    elif instance.payment_method == 'Credit':

        ## B. GESTION DU PAIEMENT CRÉDIT (lié à l'antenne)
        customer_name = instance.customer.split(',')[0] if instance.customer else "Client Inconnu"
        # Si vous n'avez pas le téléphone dans Sale, utilisez une valeur par défaut.
        customer_phone = instance.customer.split(',')[1] if instance.customer else "N/A" 
        
        # 2. Créer une instance de Créance (Credit)
        Credit.objects.create(
            nom=customer_name,
            telephone=customer_phone,
            # La date de la créance est la date de la vente
            date=instance.date or timezone.now(), 
            sale=instance,
            status='Pending'
            # Le statut par défaut est 'Pending'
            # Note: Votre modèle Credit est incomplet, il manque le montant total dû !
        )
        