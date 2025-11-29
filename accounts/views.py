from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserLoginForm, UserCreateForm, UserUpdateForm
from .models import User
from .decorators import role_required
from .permissions import Permissions

# --- LOGIN / LOGOUT ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:user_list')

    form = UserLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password']
        )
        if user:
            if user.is_blocked:
                messages.error(request, "Compte bloqué !")
            else:
                login(request, user)
                user.enregistrer_connexion()
                return redirect('index')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')

# --- CRUD UTILISATEURS ---
@login_required
@role_required('admin')
def user_list(request):
    users = User.objects.filter(is_deleted=False)
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
@role_required('admin')
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    return render(request, 'accounts/user_detail.html', {'user': user})

@login_required
@role_required('admin')
def user_create(request):
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Utilisateur créé avec succès")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Créer un utilisateur'})

@login_required
@role_required('admin')
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Utilisateur mis à jour")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Modifier utilisateur'})

@login_required
@role_required('admin')
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete(user=request.user)  # soft delete
    messages.success(request, "Utilisateur supprimé")
    return redirect('accounts:user_list')

@login_required
@role_required('admin')
def blocked_view(request):
    return render(request, 'accounts/blocked.html')

def no_permission(request):
    """
    Affiche un message d'erreur et retourne à la page précédente.
    """
    messages.error(request, "Vous n'avez pas la permission d'accéder à cette page.")
    # Redirection vers la page précédente ou vers l'accueil si aucune référence
    return redirect(request.META.get('HTTP_REFERER', '/'))