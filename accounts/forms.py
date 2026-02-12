from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Antenne, User
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
    managed_antenne = forms.ModelChoiceField(
        queryset=Antenne.objects.none(),
        required=False,
        label="Gerant d'antenne",
        help_text="Associer cet utilisateur comme gerant principal d'une antenne.",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'antenne', 'telephone', 'is_blocked']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["managed_antenne"].queryset = Antenne.objects.select_related("lieux", "gerant").order_by("nom")
        # Crispy forms helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Créer', css_class='bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded'))

    def save(self, commit=True):
        user = super().save(commit=commit)
        managed_antenne = self.cleaned_data.get("managed_antenne")

        if managed_antenne and user.pk:
            managed_antenne.gerant = user
            managed_antenne.save(update_fields=["gerant"])
            if not user.antenne_id:
                user.antenne = managed_antenne
                user.save(update_fields=["antenne"])
        return user

# --- Formulaire mise à jour utilisateur ---
class UserUpdateForm(UserChangeForm):
    password = None  # On gère le changement de mot de passe séparément
    managed_antenne = forms.ModelChoiceField(
        queryset=Antenne.objects.none(),
        required=False,
        label="Gerant d'antenne",
        help_text="Associer cet utilisateur comme gerant principal d'une antenne.",
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'antenne', 'telephone', 'is_blocked']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["managed_antenne"].queryset = Antenne.objects.select_related("lieux", "gerant").order_by("nom")
        if self.instance and self.instance.pk:
            managed = self.instance.gerant.first()
            if managed:
                self.fields["managed_antenne"].initial = managed.pk
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Enregistrer', css_class='bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded'))

    def save(self, commit=True):
        user = super().save(commit=commit)
        managed_antenne = self.cleaned_data.get("managed_antenne")

        if managed_antenne and user.pk:
            managed_antenne.gerant = user
            managed_antenne.save(update_fields=["gerant"])
            if not user.antenne_id:
                user.antenne = managed_antenne
                user.save(update_fields=["antenne"])
        return user


class AntenneForm(forms.ModelForm):
    class Meta:
        model = Antenne
        fields = ["nom", "lieux", "gerant"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gerant"].queryset = User.objects.filter(
            is_deleted=False, role=User.Role.GERANT
        ).order_by("username")

    def clean_gerant(self):
        gerant = self.cleaned_data["gerant"]
        if gerant.role != User.Role.GERANT:
            raise forms.ValidationError("Le gerant selectionne doit avoir le role 'Gerant d'antenne'.")
        return gerant
