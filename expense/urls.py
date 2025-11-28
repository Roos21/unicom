from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [

    path('', views.expense_list, name='expense_list'),
    path('create/', views.expense_create, name='expense_create'),
    path('<int:pk>/update/', views.expense_update, name='expense_update'),
    path('<int:pk>/delete/', views.expense_delete, name='expense_delete'),

    
    path('pending/', views.pending_expenses_list, name='pending_expenses'),
    path('approve/<int:expense_id>/', views.approve_expense, name='approve_expense'),
    path('reject/<int:expense_id>/', views.reject_expense, name='reject_expense'),

]
