from django import template

register = template.Library()

@register.filter
def has_permission(user, perm_name):
    """Vérifie si l'utilisateur a la permission donnée"""
    return user.has_permission(perm_name)
