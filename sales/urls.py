from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    # --- Categories ---
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_update, name='category_update'),
    path('categories/<int:pk>/validate/', views.category_validate, name='category_validate'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # --- Products ---
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_update, name='product_update'),
    path('products/<int:pk>/validate/', views.product_validate, name='product_validate'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/pricing/antenna/', views.antenna_pricing_list, name='antenna_pricing_list'),
    path('products/pricing/antenna/create/', views.antenna_pricing_create, name='antenna_pricing_create'),
    path('products/pricing/antenna/<int:pk>/edit/', views.antenna_pricing_update, name='antenna_pricing_update'),

    #Ventes

    path('ventes/', views.sale_list, name='sale_list'),  # Liste des ventes
    path('ventes/creer/', views.sale_create, name='sale_create'),  # Création d'une vente
    path('ventes/<int:pk>/modifier/', views.sale_update, name='sale_update'),  # Modification d'une vente
    path('ventes/<int:pk>/valider/', views.sale_validate, name='sale_validate'),  # Validation d'une vente
    path('ventes/<int:pk>/rejeter/', views.sale_reject, name='sale_reject'), 
    path('credits/', views.credit_list, name='credit_list'),
    path('credits/<int:pk>/paid/', views.credit_mark_paid, name='credit_mark_paid'),
    path('ventes/compte', views.rapport_periodique, name='rapport_periodique'),
    path('ventes/mon-compte', views.mon_rapport_periodique, name='mon_rapport_periodique'),
]
