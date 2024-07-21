from django.shortcuts import render, redirect
from django.views.generic import CreateView ,ListView, DetailView
from mentor.models import Mentors, Category, Specialization, Mentee, TermsAndConditions
from mentor.forms import CreateMentorForm
from django.urls import reverse_lazy, reverse
from django.db.models import Count
from django.contrib import messages
from django.core.mail import send_mail

# Create your views here.
class CreateMentor(CreateView):
    model = Mentors
    template_name = 'add_mentor.html'
    form_class = CreateMentorForm
    success_url = reverse_lazy('mentor:create_mentor')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms_and_conditions'] = TermsAndConditions.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your registration have been noted and will be in touch soon')
        return response
    
class AllMentorsView(ListView):
    model = Mentors
    template_name = 'all_mentors.html'
    context_object_name = 'mentors'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.GET.get('category')
        location = self.request.GET.get('location')

        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        
        if location:
            queryset = queryset.filter(locality=location)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['locality_choices'] = Mentors.LOCALITY_CHOICES
        return context


    
class MentorDetailView(DetailView):
    model = Mentors
    template_name = 'mentor_details.html'
    context_object_name = 'mentor'

    def post(self, request, *args, **kwargs):
        mentor = self.get_object()
        mentor_name = mentor.name
        mentor_contact = mentor.contact
        mentor_email = mentor.email
        mentee_name = request.POST.get('mentee_name')
        contact_number = request.POST.get('contact_number')
        mentee_requirement = request.POST.get('mentee_requirement')

        # Create Mentee object
        Mentee.objects.create(
            mentor_name=mentor_name,
            mentor_contact=mentor_contact,
            mentee_name=mentee_name,
            contact_number=contact_number,
            mentee_requirement=mentee_requirement
        )

        # Prepare email content
        subject = 'New Mentee Registration'
        message = f'You have a new mentee request:\n\n' \
                  f'Mentee Name: {mentee_name}\n' \
                  f'Contact Number: {contact_number}\n' \
                  f'Requirement: {mentee_requirement}'
        from_email = 'oldscool@gmail.com'
        recipient_list = [mentor_email, 'oldscool.contact@gmail.com']

        # Check if mentor_email is present and send the email
        if mentor_email:
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, 'Your response has been submitted successfully!')
            except Exception as e:
                messages.error(request, f'Mail was not delivered: {e}')
        else:
            messages.error(request, 'Mail was not delivered: Mentor email is missing.')

        # Redirect back to the same mentor details page
        return redirect(reverse('mentor:mentor_details', kwargs={'pk': mentor.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context