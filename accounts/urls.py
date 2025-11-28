from django.urls import path
from . import views

app_name = "accounts"  # Important pour le namespacing

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # CRUD Users (accessible par admin)
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_detail, name="user_detail"),
    path("users/<int:pk>/update/", views.user_update, name="user_update"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("blocked/", views.blocked_view, name="blocked"),

    path('no-permission/', views.no_permission, name='no_permission'),

]
