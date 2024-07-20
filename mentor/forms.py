from mentor.models import Mentors, Category, Specialization
from django import forms
from datetime import datetime

class CreateMentorForm(forms.ModelForm):
    class Meta:
        model = Mentors
        fields = ['name', 'contact', 'email', 'qualification', 'date_of_birth', 'experience',
                  'categories', 'specializations', 'start_weekday', 'end_weekday', 'time_from',
                  'time_to', 'image', 'instagram', 'linkedin', 'Facebook', 'locality', 'about']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control','type':'date'}),
            'experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'categories': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'specializations': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'start_weekday': forms.Select(attrs={'class': 'form-select'}),
            'end_weekday': forms.Select(attrs={'class': 'form-select'}),
            'time_from': forms.TimeInput(attrs={'class': 'form-control'}),
            'time_to': forms.TimeInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'Facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'locality': forms.Select(attrs={'class': 'form-select'}),
            'about': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False)
    specializations = forms.ModelMultipleChoiceField(queryset=Specialization.objects.all(), required=False)

    def clean(self):
        cleaned_data = super().clean()
        start_weekday = cleaned_data.get("start_weekday")
        end_weekday = cleaned_data.get("end_weekday")

        # Perform validation to ensure start_weekday is before end_weekday
        if start_weekday and end_weekday:
            weekday_choices = dict(Mentors.WEEKDAY_CHOICES)
            start_index = list(weekday_choices.keys()).index(start_weekday)
            end_index = list(weekday_choices.keys()).index(end_weekday)
            if start_index >= end_index:
                self.add_error('start_weekday', "Start weekday must be before end weekday")

        return cleaned_data