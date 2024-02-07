from django import forms
from .models import Mentee

class MenteeForm(forms.ModelForm):
    class Meta: 
        feild = [
        'mentor_name',
        'mentor_contact',
        'mentee_name',
        'contact_number',
        'mentee_requirement',
    ]
        model = Mentee
        fields = feild
