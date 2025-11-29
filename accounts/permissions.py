# auth/permissions.py

from accounts.models import User

# Rôle attendu à chaque niveau
ROLE_PER_LEVEL = {
    1: User.Role.GERANT,
    2: User.Role.DIRECTEUR,
    3: User.Role.ADMIN,
}
class Permissions:
    # Liste des permissions possibles
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"
    VIEW_DEPENSES = "view_depenses"
    VALIDATE_DEPENSES = "validate_depenses"
    VIEW_REPORTS = "view_reports"
    MANAGE_ANTENNES = "manage_antennes"
    MANAGE_TREASURY = "manage_treasury"
    MANAGE_CATEGORIES = "manage_categories"
    VALIDATE_CATEGORIES = "validate_categories"
    MANAGE_PRODUCTS = "manage_products"
    VALIDATE_PRODUCTS = "validate_products"

    VALIDATE_UPDATE_SALES = "validate_sales"  # Cette permission permettra de valider les ventes


# Rôle → permissions attribuées
ROLE_PERMISSIONS = {
    "gerant": {
        Permissions.VIEW_DEPENSES,
        Permissions.MANAGE_TREASURY,
        Permissions.MANAGE_CATEGORIES,
        Permissions.MANAGE_PRODUCTS,
        Permissions.MANAGE_ANTENNES
    },

    "admin": {
        Permissions.VIEW_USERS,
        Permissions.MANAGE_USERS,
        Permissions.MANAGE_CATEGORIES,
        Permissions.MANAGE_PRODUCTS,
        Permissions.VIEW_DEPENSES,
        Permissions.VALIDATE_DEPENSES,
        Permissions.MANAGE_TREASURY,
        Permissions.VIEW_REPORTS,
        Permissions.MANAGE_ANTENNES,
        Permissions.VALIDATE_UPDATE_SALES
    },

    "superviseur": {
        Permissions.VIEW_USERS,
        Permissions.VIEW_DEPENSES,
        Permissions.VALIDATE_DEPENSES,
    },

    "directeur": {
        Permissions.VIEW_REPORTS,
        Permissions.MANAGE_ANTENNES,
        Permissions.MANAGE_USERS,
        Permissions.VALIDATE_DEPENSES,
        Permissions.VIEW_DEPENSES,
    }
}



def has_permission(user: User, permission_name: str) -> bool:
    """
    Vérifie si l'utilisateur a la permission demandée selon son rôle.
    """
    if not user.is_authenticated:
        return False
    return permission_name in ROLE_PERMISSIONS.get(user.role, set())