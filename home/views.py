from django.shortcuts import render
from django.views.generic import View, TemplateView, ListView, CreateView
from home.models import AboutImage, Contact
from mentor.models import Category, Mentors, Specialization
from localproj.models import Project
from home.forms import ContactForm
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.contrib import messages

# how many items the home page carousels cycle through
HOME_CAROUSEL_SIZE = 8


class HomeView(View):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        # Only approved items, capped, newest first. The specializations are
        # fetched in one query (with their category, used by __str__) instead
        # of two extra queries per mentor.
        mentors = (
            Mentors.objects.filter(status=True)
            .order_by('-premium', '-pub_date')
            .only('id', 'name', 'image')
            .prefetch_related(
                Prefetch('specializations', queryset=Specialization.objects.select_related('category'))
            )[:HOME_CAROUSEL_SIZE]
        )
        projects = (
            Project.objects.filter(status=True)
            .order_by('-id')
            .only('id', 'project_name', 'description')[:HOME_CAROUSEL_SIZE]
        )
        categories = Category.objects.order_by('name')
        locality_choices_proj = [(choice[0].capitalize(), choice[1]) for choice in Project.LOCALITY_CHOICES]
        locality_choices_mentor = [(choice[0].lower(), choice[1]) for choice in Project.LOCALITY_CHOICES]
        project_names = (
            Project.objects.filter(status=True)
            .order_by('project_name')
            .values_list('project_name', flat=True)
            .distinct()
        )

        context = {
            'mentors': mentors,
            'projects': projects,
            'categories': categories,
            'locality_choices_proj': locality_choices_proj,
            'locality_choices_mentor': locality_choices_mentor,
            'project_names': project_names,
        }
        return render(request, self.template_name, context)


class TearmsAndConditionsView(TemplateView):
    template_name = 'tearms-and-conditions.html'

class EnrollView(TemplateView):
    template_name = 'enroll-now.html'
    
class AboutImageView(ListView):
    template_name = 'about.html'
    model = AboutImage
    context_object_name = 'about'
    
class ContactView(CreateView):
    template_name = 'contact.html'
    model = Contact
    form_class = ContactForm
    success_url = reverse_lazy('home:contact')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your contact form has been submitted successfully!')
        return response
    