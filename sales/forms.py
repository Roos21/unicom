# sales/forms.py
from django import forms
from .models import Category, Product, Sale
from accounts.permissions import Permissions

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'type': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Seuls certains rôles peuvent modifier le type
        if self.user and not self.user.has_permission(Permissions.MANAGE_ANTENNES):
            self.fields['type'].disabled = True


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'unit', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'price': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'unit': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'category': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter l'accès selon permissions
        if self.user:
            if not self.user.has_permission(Permissions.MANAGE_TREASURY):
                self.fields['price'].disabled = True
            if not self.user.has_permission(Permissions.MANAGE_USERS):
                self.fields['category'].queryset = Category.objects.filter(type='Bien', is_validated=True)
            else:
                # Si l'utilisateur a la permission de gérer les produits, on affiche toutes les catégories validées
                self.fields['category'].queryset = Category.objects.filter(is_validated=True)



class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['product', 'quantity', 'customer', 'payment_method', 'status']
        widgets = {
            'product': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'customer': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'payment_method': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
            'status': forms.Select(attrs={'class': 'w-full px-3 py-2 border rounded'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Afficher uniquement les produits validés
        self.fields['product'].queryset = Product.objects.filter(is_validated=True)

        # Désactiver les champs selon les permissions de l'utilisateur
        if user:
            if not user.has_permission(Permissions.MANAGE_TREASURY):
                self.fields['quantity'].disabled = True
            if not user.has_permission(Permissions.MANAGE_USERS):
                self.fields['status'].disabled = True  # Ne permet pas à l'utilisateur de modifier le statut
                self.fields['status'].initial = Sale.PENDING  # Définit le statut par défaut à "Pending" pour les utilisateurs non administrateurs

    def clean_quantity(self):
        """ Validation du champ quantity : doit être un nombre positif """
        quantity = self.cleaned_data.get('quantity')
        if quantity <= 0:
            raise forms.ValidationError("La quantité doit être un nombre positif.")
        return quantity

    def clean_total_price(self):
        """ Calcul automatique du prix total """
        product = self.cleaned_data.get('product')
        quantity = self.cleaned_data.get('quantity')

        # Vérification que le produit et la quantité sont valides
        if product and quantity:
            total_price = product.price * quantity
            return total_price
        return 0  # Si aucun produit ou quantité n'est sélectionné, on retourne 0

    def clean_status(self):
        """ Validation du champ status : ne peut être modifié par l'utilisateur non admin """
        status = self.cleaned_data.get('status')
        # Si l'utilisateur n'est pas admin, ne permet pas de changer le statut
        if status not in [Sale.PENDING, Sale.VALIDATED]:  # Autoriser seulement les statuts valides
            raise forms.ValidationError("Statut invalide.")
        return status
