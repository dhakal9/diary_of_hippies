from django import forms

class ContactForm(forms.Form):

    username = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Enter your full name'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class':'form-control',
            'placeholder':'example@email.com'
        })
    )

    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'Subject'
        })
    )

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class':'form-control',
            'rows':5,
            'placeholder':'Write your message here...'
        })
    )