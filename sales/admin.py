from django.contrib import admin
from django.urls import reverse
from .models import Category, Credit, Product, Sale
from django.utils.html import format_html
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type")
    list_filter = ("type",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "unit", "is_active")
    list_filter = ("category__type", "category")
    search_fields = ("name",)

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "total_price", "last_total_price","payment_method", "date","created_by")
    list_filter = ("product__category",)
    search_fields = ("product__name",)


@admin.action(description='Marquer les crédits sélectionnés comme Payés')
def make_paid(modeladmin, request, queryset):
    """Marque les créances comme 'Payées' et met à jour le solde si l'argent est reçu."""
    
    # NOTE: Dans un système complet, l'action de paiement devrait idéalement 
    # se faire via un formulaire dédié pour choisir le compte de réception (Caisse/Banque)
    # et créer la Transaction. Pour l'Admin, nous faisons une action simple.
    
    # 1. Mettre à jour le statut
    queryset.update(status=Credit.PAID)
    
    # 2. Logique simplifiée de réception d'argent (nécessite AccountMoney et Transaction)
    # Ceci est un exemple simpliste. Il faudra le compléter si vous voulez la mise à jour réelle du solde.
    # try:
    #     caisse = AccountMoney.objects.get(type="CAISSE")
    #     for credit in queryset:
    #         # Créer la transaction IN (Entrée)
    #         Transaction.objects.create(
    #             account=caisse,
    #             type="IN",
    #             amount=credit.amount, 
    #             sale=credit.sale # Utiliser le lien vers la vente originale
    #         )
    #         caisse.balance += credit.amount
    #     caisse.save()
    #     modeladmin.message_user(request, f"{queryset.count()} créances marquées comme payées et caisse mise à jour.", level='success')
    # except Exception as e:
    #     modeladmin.message_user(request, f"Erreur lors de la mise à jour du compte: {e}", level='error')
    
    modeladmin.message_user(request, f"{queryset.count()} créances marquées comme Payées.", level='success')


@admin.register(Credit)
class CreditAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 
        'telephone', 
        'montant_du', 
        'date_creance',
        'status', 
        'lien_vers_la_vente'
    )
    list_filter = ('status', 'date')
    search_fields = ('nom', 'telephone', 'sale__product__name')
    readonly_fields = ('date',)
    actions = [make_paid] # Ajouter l'action de masse

    def montant_du(self, obj):
        if obj.sale:
            return f"{obj.sale.total_price} FCFA"
        
        return "Montant Non Défini" # Ou 0.00 FCFA
    montant_du.short_description = "Montant Dû"

    def date_creance(self, obj):
        # Afficher la date formatée
        return obj.date.strftime("%d %b %Y")
    date_creance.short_description = "Date"

    def lien_vers_la_vente(self, obj):
        """Crée un lien vers la vente associée dans l'interface Admin."""
        if obj.sale:
            url = reverse("admin:sales_sale_change", args=[obj.sale.id]) # Assurez-vous que 'sales' est le nom de l'app de Sale
            return format_html('<a href="{}">Voir Vente #{}</a>', url, obj.sale.id)
        return "-"
    lien_vers_la_vente.short_description = "Vente Source"
    
    # Définir l'appartenance à un Fieldset pour la vue détaillée (optionnel)
    fieldsets = (
        (None, {'fields': ('nom', 'telephone', 'date', 'status')}),
        ('Détails de la Créance', {'fields': ('sale',)}),
    )