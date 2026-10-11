from datetime import timedelta

from django import forms
from django.utils import timezone

from connect.models import Booking, Message, Review, slots_for
from localproj.models import Milestone
from mentor.models import Mentors, validate_phone_number


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'you@example.com', 'autocomplete': 'email', 'autofocus': True,
    }))


class BookingForm(forms.ModelForm):
    """
    Request a call. With a mentor schedule the visitor must pick one of the free slots;
    without one they give a preferred date and a free-text time.
    """

    contact_number = forms.CharField(max_length=15, validators=[validate_phone_number])
    start_time = forms.TimeField(required=False, input_formats=['%H:%M'])

    class Meta:
        model = Booking
        fields = ['kind', 'mentee_name', 'email', 'contact_number', 'requirement', 'date', 'start_time', 'preferred_time']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, mentor, **kwargs):
        self.mentor = mentor
        super().__init__(*args, **kwargs)
        if mentor.free_intro:
            self.fields['kind'].initial = Booking.INTRO  # start with the no-commitment option
        else:
            self.fields['kind'].choices = [(Booking.SESSION, 'Mentoring session')]
        self.fields['requirement'].label = 'What do you need help with?'

    def clean_date(self):
        day = self.cleaned_data['date']
        today = timezone.localdate()
        if day < today or day > today + timedelta(days=60):
            raise forms.ValidationError('Pick a date within the next 60 days.')
        return day

    def clean(self):
        cleaned = super().clean()
        day, start = cleaned.get('date'), cleaned.get('start_time')
        if not day:
            return cleaned
        if self.mentor.has_schedule:
            if not start:
                self.add_error('start_time', 'Pick a time slot.')
            elif start not in slots_for(self.mentor, day):
                self.add_error('start_time', 'That slot was just taken or is no longer available. Pick another.')
        else:
            cleaned['start_time'] = None
        return cleaned

    def save(self, commit=True):
        booking = super().save(commit=False)
        booking.mentor = self.mentor
        if commit:
            booking.save()
        return booking


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(i, i) for i in range(5, 0, -1)], coerce=int, widget=forms.RadioSelect
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {'comment': forms.Textarea(attrs={
            'class': 'form-control', 'rows': 3, 'placeholder': 'What was helpful? (optional)',
        })}


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'due_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. First design draft'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class MentorProfileForm(forms.ModelForm):
    """What a logged-in mentor can change themselves (not approval, verification or premium)."""

    class Meta:
        model = Mentors
        fields = [
            'name', 'headline', 'image', 'about', 'qualification', 'experience', 'languages',
            'categories', 'specializations', 'locality', 'contact',
            'start_weekday', 'end_weekday', 'time_from', 'time_to', 'session_minutes',
            'free_intro', 'price_per_session', 'instagram', 'linkedin', 'Facebook',
        ]
        widgets = {
            'about': forms.Textarea(attrs={'rows': 4}),
            'time_from': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'time_to': forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
            'categories': forms.SelectMultiple(attrs={'size': 6}),
            'specializations': forms.SelectMultiple(attrs={'size': 8}),
        }
        labels = {'Facebook': 'Facebook', 'contact': 'Phone (shared only after you accept a request)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
        self.fields['specializations'].queryset = self.fields['specializations'].queryset.select_related('category')

    def clean(self):
        cleaned = super().clean()
        start, end = cleaned.get('time_from'), cleaned.get('time_to')
        if start and end and end <= start:
            self.add_error('time_to', 'End time must be after the start time.')
        return cleaned


class InviteForm(forms.Form):
    project = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-select'}))
    note = forms.CharField(required=False, max_length=500, widget=forms.Textarea(attrs={
        'class': 'form-control', 'rows': 2, 'placeholder': 'Add a note (optional)',
    }))

    def __init__(self, *args, projects, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['project'].queryset = projects
