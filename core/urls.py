
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    """
    Page d'accueil / tableau de bord de l'ERP
    """
    return render(request, 'index.html')
urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),  # <--- Ici
    path("sales/", include("sales.urls", namespace="sales")),  # <--- Ici
    path("expenses/", include("expense.urls", namespace="expenses")),  # <--- Ici
    
    path('', index, name='index'),
]
