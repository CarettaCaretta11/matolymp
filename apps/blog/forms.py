from django import forms

from .models import Submission
from .models import User


class SubmissionForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Submission title"}),
        required=True,
        min_length=1,
        max_length=250,
    )

    content = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": "3", "placeholder": "Optional text"}),
        max_length=5000,
        required=False,
    )

    class Meta:
        model = Submission
        fields = ("title", "content")
