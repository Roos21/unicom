from django import forms
from .models import Expense, ExpenseCategory, AccountMoney
from accounts.permissions import Permissions
from .models import *

TW_INPUT = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
TW_TEXTAREA = "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
TW_SELECT = "w-full px-3 py-2 border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-blue-500"


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "category", "account", "amount", "description", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": TW_INPUT}),
            "category": forms.Select(attrs={"class": TW_SELECT}),
            "account": forms.Select(attrs={"class": TW_SELECT}),
            "amount": forms.NumberInput(attrs={"class": TW_INPUT}),
            "description": forms.Textarea(attrs={"class": TW_TEXTAREA + " h-24"}),
            "status": forms.Select(attrs={"class": TW_SELECT}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Afficher seulement les catégories autorisées
        self.fields["category"].queryset = ExpenseCategory.objects.all()

        # Afficher seulement les comptes existants
        self.fields["account"].queryset = AccountMoney.objects.all()

        # Permissions : un utilisateur sans MANAGE_TREASURY ne peut rien modifier
        if not self.user.has_permission(Permissions.MANAGE_TREASURY):
            for field in self.fields:
                self.fields[field].disabled = True

        # Statut modifiable seulement par VALIDATE_DEPENSES
        if not self.user.has_permission(Permissions.VALIDATE_DEPENSES):
            self.fields["status"].disabled = True
            self.fields["status"].initial = "PENDING"


class ValidationThresholdForm(forms.ModelForm):
    class Meta:
        model = ValidationThreshold
        fields = ["min_amount", "max_amount", "approver", "level"]
        widgets = {
            "min_amount": forms.NumberInput(attrs={"class": TW_INPUT}),
            "max_amount": forms.NumberInput(attrs={"class": TW_INPUT}),
            "approver": forms.Select(attrs={"class": TW_SELECT}),
            "level": forms.NumberInput(attrs={"class": TW_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Si l'utilisateur n'est pas autorisé, il ne peut rien changer
        if not user.has_permission(Permissions.MANAGE_USERS):
            for field in self.fields:
                self.fields[field].disabled = True


class ApprovalStepForm(forms.ModelForm):
    action = forms.ChoiceField(
        choices=[("approve", "Approuver"), ("reject", "Rejeter")],
        widget=forms.RadioSelect(attrs={"class": "space-x-4"})
    )

    class Meta:
        model = ApprovalStep
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"class": TW_TEXTAREA + " h-20"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not self.user.has_permission(Permissions.VALIDATE_DEPENSES):
            self.fields["comment"].disabled = True
            self.fields["action"].disabled = True

    def save(self, commit=True):
        step = super().save(commit=False)
        action = self.cleaned_data["action"]

        step.approved = action == "approve"
        step.rejected = action == "reject"

        return super().save(commit=commit)

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["account", "type", "amount"]
        widgets = {
            "account": forms.Select(attrs={"class": TW_SELECT}),
            "type": forms.Select(attrs={"class": TW_SELECT}),
            "amount": forms.NumberInput(attrs={"class": TW_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not user.has_permission(Permissions.MANAGE_TREASURY):
            for field in self.fields:
                self.fields[field].disabled = True


class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": TW_INPUT}),
            "description": forms.Textarea(attrs={"class": TW_TEXTAREA + " h-20"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if not user.has_permission(Permissions.MANAGE_CATEGORIES):
            for field in self.fields:
                self.fields[field].disabled = True
