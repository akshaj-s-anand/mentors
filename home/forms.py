# forms.py
from django import forms
from home.models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'phone_number', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your message', 'rows': 5}),
        }

    def clean_phone_number(self):
        # the page's JS restricts input too, but that is easy to bypass
        phone_number = self.cleaned_data['phone_number'].strip()
        if not (phone_number.isdigit() and len(phone_number) == 10):
            raise forms.ValidationError('Enter a 10 digit phone number.')
        return phone_number
