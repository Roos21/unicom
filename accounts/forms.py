from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

# --- Formulaire de connexion ---
class UserLoginForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Nom d’utilisateur'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Se connecter', css_class='w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 rounded'))

# --- Formulaire création utilisateur ---
class UserCreateForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'antenne', 'telephone', 'is_blocked']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Crispy forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Créer', css_class='bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded'))

# --- Formulaire mise à jour utilisateur ---
class UserUpdateForm(UserChangeForm):
    password = None  # On gère le changement de mot de passe séparément

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'antenne', 'telephone', 'is_blocked']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded'))
