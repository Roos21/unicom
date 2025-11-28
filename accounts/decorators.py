# auth/decorators.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
    """
    Decorator to check if the user has one of the required roles.
    If not authenticated or not in the allowed roles, redirect to the no_permission page.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")  # Redirige l'utilisateur vers la page de login si non authentifié

            if request.user.role not in roles:
                messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
                return redirect("accounts:no_permission")  # Redirige vers une page d'absence de permission

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission):
    """
    Decorator to check if the user has the required permission.
    If not authenticated or lacks permission, return a forbidden response.
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect("accounts:login")  # Redirige l'utilisateur vers la page de login si non authentifié

            if not user.has_permission(permission):
                messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
                return redirect("accounts:no_permission")  # Redirige vers la page de permission manquante

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
