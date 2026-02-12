import django_filters
from .models import Sale
from accounts.models import Antenne

class SaleFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(field_name='product__name', lookup_expr='icontains', label="Produit")
    customer = django_filters.CharFilter(lookup_expr='icontains', label="Client")
    status = django_filters.ChoiceFilter(choices=Sale.SALE_STATUS_CHOICES, label="Statut")
    created_at = django_filters.DateFromToRangeFilter(label="Date (du ... au ...)")
    antenne = django_filters.ModelChoiceFilter(
        field_name='created_by__antenne',
        queryset=Antenne.objects.all(),
        label="Antenne"
    )

    

    class Meta:
        model = Sale
        fields = ['product', 'customer', 'status', 'created_at', 'antenne']
