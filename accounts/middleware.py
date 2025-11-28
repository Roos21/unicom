from django.shortcuts import redirect
from django.urls import reverse

class BlockedUserMiddleware:
    """
    Middleware pour empêcher les utilisateurs bloqués d'accéder à l'application.
    - Si is_blocked = True, redirige vers une page 'blocked'.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        # Ignorer si l'utilisateur n'est pas connecté
        if user.is_authenticated and user.is_blocked:
            # Ignorer la page de logout pour éviter boucle infinie
            if request.path != reverse('accounts:logout') and request.path != reverse('accounts:blocked'):
                return redirect('accounts:blocked')

        return self.get_response(request)
