from django.shortcuts import render
from django.views.generic import View, TemplateView, ListView, CreateView
from home.models import AboutImage, Contact
from mentor.models import Category, Specialization, Mentee, Mentors
from localproj.models import Project, Comment
from home.forms import ContactForm
from django.urls import reverse_lazy
from django.db.models import Count
from django.contrib import messages

# Create your views here.


class HomeView(View):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        mentors = Mentors.objects.filter(status=True)
        projects = Project.objects.filter(status=True)
        categories = Category.objects.all()
        locality_choices = [(choice[0].lower(), choice[1]) for choice in Project.LOCALITY_CHOICES]
        project_names = Project.objects.values_list('project_name', flat=True).distinct()
        
        context = {
            'mentors': mentors,
            'projects': projects,
            'categories': categories,
            'locality_choices': locality_choices,
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
    