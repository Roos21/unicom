import django_filters
from .models import Sale

class SaleFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains', label="Produit")
    customer = django_filters.CharFilter(lookup_expr='icontains', label="Client")
    status = django_filters.ChoiceFilter(choices=Sale.SALE_STATUS_CHOICES, label="Statut")
    created_at = django_filters.DateFromToRangeFilter(label="Date (du ... au ...)")

    

    class Meta:
        model = Sale
        fields = ['product', 'customer', 'status', 'created_at']
