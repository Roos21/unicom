from django.contrib import admin
from django.utils.html import format_html
from .models import AccountMoney, ExpenseCategory, ValidationThreshold, Expense, Transaction, ApprovalStep
from django.conf import settings

# ---------------------------------------------
# 1. Compte (Caisse / Banque)
# ---------------------------------------------
@admin.register(AccountMoney)
class AccountMoneyAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'balance')
    list_filter = ('type',)
    search_fields = ('name',)

# ---------------------------------------------
# 2. Catégorie de dépenses
# ---------------------------------------------
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# ---------------------------------------------
# 3. Seuil de validation
# ---------------------------------------------
@admin.register(ValidationThreshold)
class ValidationThresholdAdmin(admin.ModelAdmin):
    list_display = ('level', 'min_amount', 'max_amount', 'approver')
    list_filter = ('level',)
    search_fields = ('approver__username',)

# ---------------------------------------------
# 4. Dépense
# ---------------------------------------------
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'account', 'status_colored', 'created_by', 'created_at')
    list_filter = ('status', 'account', 'category')
    search_fields = ('title', 'created_by__username')
    readonly_fields = ('created_at',)

    def status_colored(self, obj):
        """Affichage coloré du statut dans l'admin"""
        color_map = {
            "PENDING": "orange",
            "IN_REVIEW": "blue",
            "APPROVED": "green",
            "REJECTED": "red",
            "PAID": "gray"
        }
        color = color_map.get(obj.status, "black")
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_colored.short_description = 'Statut'

# ---------------------------------------------
# 5. Transaction
# ---------------------------------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'type', 'amount', 'expense', 'created_at')
    list_filter = ('type', 'account')
    search_fields = ('expense__title',)

# ---------------------------------------------
# 6. ApprovalStep (multi-niveaux)
# ---------------------------------------------
@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    list_display = ('expense', 'level', 'approver', 'approved', 'rejected', 'validated_at')
    list_filter = ('approved', 'rejected', 'level')
    search_fields = ('expense__title', 'approver__username')
