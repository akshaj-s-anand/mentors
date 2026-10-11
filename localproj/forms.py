from django import forms
from localproj.models import Project, Comment
from mentor.models import Specialization, validate_phone_number


class CreateProjectForm(forms.ModelForm):
    """Posted by a logged-in mentor; `posted_by` is set from the session, not chosen in the form."""

    class Meta:
        model = Project
        fields = ['project_name', 'description', 'skills', 'budget', 'location', 'start_date', 'end_date']
        labels = {
            'project_name': 'Project title',
            'description': 'What needs to be done?',
            'skills': 'Skills needed',
            'budget': 'Budget',
            'location': 'Location',
            'start_date': 'Start Date',
            'end_date': 'Deadline',
        }
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 120,
                                                   'placeholder': 'e.g. Logo and brand kit for a bakery'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'skills': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 6}),
            'budget': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹15,000 (optional)'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True
        self.fields['skills'].queryset = Specialization.objects.select_related('category').order_by('specialist')

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('start_date'), cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', 'The deadline must be after the start date.')
        return cleaned


class CommentForm(forms.ModelForm):
    """A proposal for a project."""

    phone_number = forms.CharField(max_length=15, validators=[validate_phone_number])

    class Meta:
        model = Comment
        fields = ['name', 'phone_number', 'email', 'response', 'proposed_price', 'timeline']
