# forms.py
from django import forms
from django.core.validators import FileExtensionValidator
from localproj.models import Project, Comment
from mentor.models import Mentors

class CreateProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['project_name', 'posted_by', 'location', 'start_date', 'end_date', 'description']
        labels = {
            'project_name': 'Project Name',
            'posted_by': 'Posted By',
            'location': 'Location',
            'start_date': 'Start Date',
            'end_date': 'End Date',
            'description': 'Description',
        }
        widgets = {
            'posted_by': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(CreateProjectForm, self).__init__(*args, **kwargs)
        # Queryset for posted_by field
        self.fields['posted_by'].queryset = Mentors.objects.all()
        
        # Get distinct project names
        distinct_project_names = Project.objects.values_list('project_name', flat=True).distinct()
        project_name_choices = [(project_name, project_name) for project_name in distinct_project_names]
        
        # Set choices for project_name field
        self.fields['project_name'] = forms.ChoiceField(
            choices=project_name_choices,
            widget=forms.Select(attrs={'class': 'form-control'})
        )

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'phone_number', 'email', 'response']