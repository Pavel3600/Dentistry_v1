import re
from django import forms
from django.core.exceptions import ValidationError


def validate_route(value):
    if not re.match(r'^[a-z0-9-]+$', value):
        raise ValidationError(
            "Only lowercase Latin letters, numbers and hyphens are allowed"
        )


class CategoryForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        label="Category Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter a category name'
        })
    )

    route = forms.CharField(
        max_length=255,
        label="URL route (in Latin)",
        validators=[validate_route],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'bread-milk-cakes'
        })
    )

    image = forms.CharField(
        max_length=255,
        label="Image file name",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'cakes.png'
        })
    )