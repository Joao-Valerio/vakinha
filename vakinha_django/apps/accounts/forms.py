from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="Nome",
        widget=forms.TextInput(attrs={"placeholder": "Seu nome"}),
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        label="Sobrenome",
        widget=forms.TextInput(attrs={"placeholder": "Seu sobrenome"}),
    )
    email = forms.EmailField(
        required=True,
        label="E-mail",
        widget=forms.EmailInput(attrs={"placeholder": "seu@email.com"}),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name", "username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Nome de usuário"}),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este e-mail já está cadastrado.")
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuário ou E-mail",
        widget=forms.TextInput(attrs={"placeholder": "Usuário ou e-mail", "autofocus": True}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"placeholder": "Sua senha"}),
    )


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50, required=True, label="Nome")
    last_name = forms.CharField(max_length=50, required=False, label="Sobrenome")
    email = forms.EmailField(required=True, label="E-mail")

    class Meta:
        model = UserProfile
        fields = ("avatar", "bio", "phone", "cpf_cnpj")
        labels = {
            "bio": "Sobre você",
            "phone": "Telefone",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Fale um pouco sobre você..."}),
            "phone": forms.TextInput(attrs={"placeholder": "(11) 99999-9999"}),
            "cpf_cnpj": forms.TextInput(attrs={"placeholder": "000.000.000-00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile.save()
        return profile
