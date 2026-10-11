from django.conf import settings
from django.db.models import Case, Count, Q, Value, When
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, DetailView
from localproj.models import Comment, Project, TermsAndConditions
from localproj.forms import CreateProjectForm, CommentForm
from django.contrib import messages
from home.mixins import AjaxListMixin
from connect import notify
from connect.auth import current_mentor, mentor_required


@method_decorator(mentor_required, name='dispatch')
class CreateProject(CreateView):
    model = Project
    template_name = 'add_project.html'
    form_class = CreateProjectForm
    success_url = reverse_lazy('connect:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['terms_and_conditions'] = TermsAndConditions.objects.all()
        return context

    def form_valid(self, form):
        form.instance.posted_by = current_mentor(self.request)
        response = super().form_valid(form)
        notify.email(self.request, settings.SITE_NOTIFY_EMAIL, 'New project to approve', [
            f'{form.instance.posted_by.name} posted "{form.instance.project_name}". Approve it in the admin.',
        ])
        messages.success(self.request, 'Project submitted! It will appear on the site once our team approves it.')
        return response


class AllProjectsView(AjaxListMixin, ListView):
    template_name = 'all_projects.html'
    partial_template_name = 'partials/project_results.html'
    context_object_name = 'projects'

    def get_queryset(self):
        # only projects approved by an admin are public
        queryset = (
            Project.objects.filter(status=True)
            .only('id', 'project_name', 'location', 'description', 'budget', 'stage', 'end_date')
            .annotate(
                proposal_count=Count('comments', distinct=True),
                stage_order=Case(
                    When(stage=Project.STAGE_OPEN, then=Value(0)),
                    When(stage=Project.STAGE_IN_PROGRESS, then=Value(1)),
                    default=Value(2),
                ),
            )
            .order_by('stage_order', '-id')  # open projects first
        )
        project_name = self.request.GET.get('project_name')
        location = self.request.GET.get('location')
        query = self.request.GET.get('q', '').strip()[:100]
        stage = self.request.GET.get('stage')

        if project_name:
            queryset = queryset.filter(project_name=project_name)
        if location:
            queryset = queryset.filter(location=location)
        if stage in dict(Project.STAGE_CHOICES):
            queryset = queryset.filter(stage=stage)
        if query:
            queryset = queryset.filter(
                Q(project_name__icontains=query) | Q(description__icontains=query)
                | Q(skills__specialist__icontains=query)
            ).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project_names'] = (
            Project.objects.filter(status=True)
            .order_by('project_name')
            .values_list('project_name', flat=True)
            .distinct()
        )
        context['locations'] = [loc[0] for loc in Project.LOCALITY_CHOICES]
        context['stages'] = Project.STAGE_CHOICES
        return context


class ProjectDetails(DetailView):
    template_name = 'project.html'
    context_object_name = 'project'

    def get_queryset(self):
        return Project.objects.filter(status=True).select_related('posted_by').prefetch_related('skills')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('form', CommentForm())
        context['proposal_count'] = self.object.comments.count()
        context['is_owner'] = current_mentor(self.request) == self.object.posted_by
        return context


@require_POST
def add_comment(request, pk):
    """Submit a proposal. The proposer gets a private link to follow it, chat and see milestones."""
    project = get_object_or_404(Project.objects.select_related('posted_by'), pk=pk, status=True)
    if project.stage != Project.STAGE_OPEN:
        messages.error(request, 'This project is no longer taking proposals.')
        return redirect('localproj:project_details', pk=pk)

    form = CommentForm(request.POST)
    if form.is_valid():
        proposal = form.save(commit=False)
        proposal.post = project
        proposal.save()

        proposal_url = reverse('connect:proposal_client', args=[proposal.token])
        notify.email(request, proposal.email, f'Proposal sent for "{project.project_name}"', [
            f'Hi {proposal.name},', '',
            'Your proposal has been sent. Keep this link: it is your private page to follow it,',
            'chat with the project owner and see milestones if you are chosen.',
        ], proposal_url, 'Your proposal')
        notify.email(request, project.posted_by.email, f'New proposal for "{project.project_name}"', [
            f'{proposal.name} sent a proposal' + (f' ({proposal.proposed_price})' if proposal.proposed_price else '') + ':',
            '', proposal.response,
        ], reverse('connect:proposal_owner', args=[proposal.pk]), 'Review it')

        messages.success(request, 'Proposal sent! We emailed you a link to follow it.')
        return redirect(proposal_url)

    # show the form again with its errors and the visitor's input kept
    return render(request, 'project.html', {
        'form': form, 'project': project, 'proposal_count': project.comments.count(),
    }, status=400)
