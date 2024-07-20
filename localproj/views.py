from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView, DetailView
from localproj.models import Project, TermsAndConditions
from localproj.forms import CreateProjectForm, CommentForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count

# Create your views here.
class CreateProject(CreateView):
    model = Project
    template_name = 'add_project.html'
    form_class = CreateProjectForm
    success_url = reverse_lazy('home:home')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms_and_conditions'] = TermsAndConditions.objects.all()
        return context
    
class AllProjectsView(ListView):
    model = Project
    template_name = 'all_projects.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = super().get_queryset().filter(status=True)  # Filter projects with status=True
        project_name = self.request.GET.get('project_name')
        location = self.request.GET.get('location')

        if project_name:
            queryset = queryset.filter(project_name=project_name)
        
        if location:
            queryset = queryset.filter(location=location)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all project names from the Project model
        project_names = Project.objects.values_list('project_name', flat=True).distinct()
        context['project_names'] = project_names
        context['locations'] = [loc[0] for loc in Project.LOCALITY_CHOICES]
        return context


class ProjectDetails(DetailView):
    model = Project
    template_name = 'project.html'
    context_object_name = 'project'
    
def add_comment(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = project  # Associate comment with the project
            comment.save()
            messages.success(request, 'Your comment has been added successfully.')
            return redirect('localproj:project_details', pk=pk)  # Redirect to project details page
    else:
        form = CommentForm()
    
    return render(request, 'project.html', {'form': form, 'project': project})