from datetime import timedelta

from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView, DetailView
from mentor.models import Mentors, Category, Specialization, TermsAndConditions
from mentor.forms import CreateMentorForm
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from home.mixins import AjaxListMixin
from connect.auth import current_mentor
from connect.forms import BookingForm, InviteForm
from connect.models import mentor_stats, rating_annotations
from localproj.models import Project

# card skill chips: specializations with their category (used by Specialization.__str__)
SPECIALIZATIONS_PREFETCH = Prefetch('specializations', queryset=Specialization.objects.select_related('category'))


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


class AllMentorsView(AjaxListMixin, ListView):
    template_name = 'all_mentors.html'
    partial_template_name = 'partials/mentor_results.html'
    context_object_name = 'mentors'

    def get_skill(self):
        """Skill landing pages (/mentor/skills/<id>-<slug>/) preset the skill filter."""
        if not hasattr(self, '_skill'):
            skill_id = self.kwargs.get('skill_id') or self.request.GET.get('skill')
            self._skill = (
                Specialization.objects.select_related('category').filter(pk=skill_id).first()
                if str(skill_id or '').isdigit() else None
            )
        return self._skill

    def get_queryset(self):
        # only mentors approved by an admin are public
        queryset = (
            Mentors.objects.filter(status=True)
            .only('id', 'slug', 'name', 'image', 'locality', 'about', 'headline', 'verified',
                  'free_intro', 'price_per_session', 'premium', 'pub_date')
            .annotate(**rating_annotations())
            .prefetch_related(SPECIALIZATIONS_PREFETCH)
            .order_by('-premium', '-verified', '-pub_date')
        )
        category_id = self.request.GET.get('category')
        location = self.kwargs.get('district') or self.request.GET.get('location')
        query = self.request.GET.get('q', '').strip()[:100]

        if category_id and category_id.isdigit():
            queryset = queryset.filter(categories__id=category_id)
        if location:
            queryset = queryset.filter(locality=location)
        if self.get_skill():
            queryset = queryset.filter(specializations=self.get_skill())
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(headline__icontains=query) | Q(about__icontains=query)
                | Q(qualification__icontains=query) | Q(specializations__specialist__icontains=query)
                | Q(categories__name__icontains=query)
            )
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.order_by('name')
        context['locality_choices'] = Mentors.LOCALITY_CHOICES
        context['skill'] = self.get_skill()
        district = self.kwargs.get('district')
        context['district_label'] = dict(Mentors.LOCALITY_CHOICES).get(district, '') if district else ''
        return context


def mentor_by_id(request, pk):
    mentor = get_object_or_404(Mentors, pk=pk, status=True)
    return redirect(mentor, permanent=True)


class MentorDetailView(DetailView):
    template_name = 'mentor_details.html'
    context_object_name = 'mentor'

    def get_queryset(self):
        return Mentors.objects.filter(status=True).prefetch_related(SPECIALIZATIONS_PREFETCH)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = self.object
        context.setdefault('booking_form', BookingForm(mentor=mentor))
        context['stats'] = mentor_stats(mentor)
        context['reviews'] = mentor.reviews.filter(is_public=True)[:10]
        today = timezone.localdate()
        context['date_min'] = today.isoformat()
        context['date_max'] = (today + timedelta(days=60)).isoformat()

        # a logged-in mentor can invite this mentor to one of their open projects
        viewer = current_mentor(self.request)
        if viewer and viewer.pk != mentor.pk:
            open_projects = Project.objects.filter(posted_by=viewer, status=True, stage=Project.STAGE_OPEN)
            if open_projects.exists():
                context['invite_form'] = InviteForm(projects=open_projects)
        return context
