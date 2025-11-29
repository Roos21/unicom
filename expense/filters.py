import django_filters
from django import forms
from .models import Expense

class ExpenseFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Titre',
        widget=forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-2 py-1'})
    )
    
    status = django_filters.ChoiceFilter(
        choices=Expense.STATUS,
        label='Statut',
        widget=forms.Select(attrs={'class': 'border border-gray-300 rounded px-2 py-1'})
    )

    created_at = django_filters.DateFromToRangeFilter(label="Date (du ... au ...)")


    class Meta:
        model = Expense
        fields = ['title', 'status', 'created_at']
