from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin personnalisé pour notre User"""

    # Champs affichés dans la liste
    list_display = ("username", "email", "role", "is_active", "is_blocked", "date_creation")
    list_filter = ("role", "is_active", "is_blocked", "is_staff")
    search_fields = ("username", "email", "telephone", "antenne")
    ordering = ("username",)

    # Champs visibles dans l'édition du User
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "telephone", "antenne")}),
        (_("Permissions"), {"fields": ("role", "is_active", "is_blocked", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login",)}),  # on enlève date_creation
    )


    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "role", "password1", "password2", "is_active", "is_staff"),
        }),
    )
