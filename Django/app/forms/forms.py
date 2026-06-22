from django import forms


class UserForm(forms.Form):
    name = forms.CharField(
        label="Client Name",
        min_length=3
    )

    age = forms.IntegerField(
        label="Customer Age",
        min_value=1,
        max_value=100
    )