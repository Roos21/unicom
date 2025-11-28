from django import template

register = template.Library()

@register.filter
def in_list(value, arg):
    """Vérifie si la valeur est dans une liste/tuple séparé par des virgules"""
    return value in arg.split(',')
