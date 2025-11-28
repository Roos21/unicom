from django import template
from accounts.permissions import ROLE_PERMISSIONS

register = template.Library()

@register.simple_tag
def role_permissions(role):
    """Retourne la liste des permissions du rôle."""
    return ROLE_PERMISSIONS.get(role, set())
