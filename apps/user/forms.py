from django import forms
from django.core.validators import RegexValidator

from .models import User


class UserForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "first_name", "placeholder": "first name (optional)", "type": "text"}
        ),
        min_length=1,
        max_length=12,
        required=False,
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "last_name", "placeholder": "last name (optional)", "type": "text"}
        ),
        min_length=1,
        max_length=12,
        required=False,
    )

    alphanumeric = RegexValidator(
        r"^[0-9a-zA-Z_]*$", "This value may contain only letters, " "numbers and _ characters."
    )
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "username", "required": "", "autofocus": ""}
        ),
        max_length=12,
        min_length=3,
        required=True,
        validators=[alphanumeric],
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "id": "email", "placeholder": "email", "type": "text"}
        ),
        required=False,
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "password", "required": ""}),
        min_length=4,
        required=True,
    )

    about_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "id": "about_me",
                "rows": "3",
                "placeholder": "about yourself (recommended)",
            }
        ),
        max_length=500,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "about_text",
        )


class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "first_name", "placeholder": "first name (optional)", "type": "text"}
        ),
        min_length=1,
        max_length=12,
        required=False,
    )

    last_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "id": "last_name", "placeholder": "last name (optional)", "type": "text"}
        ),
        min_length=1,
        max_length=12,
        required=False,
    )

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "id": "email", "placeholder": "email", "type": "text"}
        ),
        required=False,
    )

    about_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "id": "about_me",
                "rows": "3",
                "placeholder": "about yourself (recommended)",
            }
        ),
        max_length=500,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "about_text",
        )
