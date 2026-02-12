from django import forms

from accounts.models import Antenne
from accounts.permissions import Permissions
from .models import Category, Product, ProductByAntenne, Sale


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "type": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and not self.user.has_permission(Permissions.MANAGE_ANTENNES):
            self.fields["type"].disabled = True


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "standard_price", "unit", "category", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "standard_price": forms.NumberInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "unit": forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "category": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_validated=True)


class ProductByAntenneForm(forms.ModelForm):
    class Meta:
        model = ProductByAntenne
        fields = ["product", "antenne", "price", "is_active"]
        widgets = {
            "product": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "antenne": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "price": forms.NumberInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "is_active": forms.CheckboxInput(attrs={"class": "h-4 w-4"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].queryset = Product.objects.filter(is_active=True, is_validated=True).order_by("name")
        self.fields["antenne"].queryset = Antenne.objects.all().order_by("nom")


class SaleForm(forms.ModelForm):
    credit_nom = forms.CharField(required=False, label="Nom client credit")
    credit_telephone = forms.CharField(required=False, label="Telephone client credit")

    class Meta:
        model = Sale
        fields = ["product", "quantity", "customer", "payment_method", "status"]
        widgets = {
            "product": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "quantity": forms.NumberInput(attrs={"class": "w-full px-3 py-2 border rounded", "min": 1}),
            "customer": forms.TextInput(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "payment_method": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
            "status": forms.Select(attrs={"class": "w-full px-3 py-2 border rounded"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.user = user

        self.fields["product"].queryset = Product.objects.filter(is_validated=True, is_active=True).order_by("name")

        if user and not user.has_permission(Permissions.VALIDATE_UPDATE_SALES):
            self.fields["status"].disabled = True
            self.fields["status"].initial = Sale.PENDING

        if self.instance and self.instance.pk and self.instance.payment_method == "Credit":
            credit = getattr(self.instance, "credit", None)
            if credit:
                self.fields["credit_nom"].initial = credit.nom
                self.fields["credit_telephone"].initial = credit.telephone

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None or quantity <= 0:
            raise forms.ValidationError("La quantite doit etre positive.")
        return quantity

    def clean(self):
        cleaned = super().clean()
        payment_method = cleaned.get("payment_method")

        if payment_method == "Credit":
            credit_nom = cleaned.get("credit_nom") or cleaned.get("customer")
            if not credit_nom:
                self.add_error("credit_nom", "Le nom du client credit est requis.")

        return cleaned


class ReportingPeriodForm(forms.Form):
    PERIOD_CHOICES = (
        ("day", "Jour"),
        ("week", "7 jours"),
        ("month", "Mois"),
        ("quarter", "Trimestre"),
        ("year", "Annee"),
    )

    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label="Periode",
        widget=forms.Select(attrs={"class": "form-select p-2 border rounded-md"}),
    )
    antenne = forms.ModelChoiceField(
        queryset=Antenne.objects.none(),
        required=False,
        empty_label="Toutes les antennes",
        label="Antenne",
        widget=forms.Select(attrs={"class": "form-select p-2 border rounded-md"}),
    )

    def __init__(self, *args, **kwargs):
        antennes_qs = kwargs.pop("antennes_qs", Antenne.objects.all())
        super().__init__(*args, **kwargs)
        self.fields["antenne"].queryset = antennes_qs
