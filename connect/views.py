from datetime import date as date_cls

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from connect import notify
from connect.auth import (
    current_mentor, login_mentor, logout_mentor, make_login_token, mentor_required, read_login_token,
)
from connect.forms import (
    BookingForm, InviteForm, LoginForm, MentorProfileForm, MessageForm, MilestoneForm, ReviewForm,
)
from connect.models import Booking, Message, Review, mentor_stats, slots_for
from localproj.models import Comment, Milestone, Project
from mentor.models import Mentors, whatsapp_number


# --------------------------------------------------------------------------
# Login with an emailed link
# --------------------------------------------------------------------------

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or ''
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = ''
    if current_mentor(request):
        return redirect(next_url or 'connect:dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        mentor = Mentors.objects.filter(email__iexact=form.cleaned_data['email'], status=True).first()
        if mentor:
            link = reverse('connect:login_link', args=[make_login_token(mentor)])
            if next_url:
                link += f'?next={next_url}'
            notify.email(request, mentor.email, 'Your login link', [
                f'Hi {mentor.name},', '', 'Use this link to log in to your Oldscool dashboard.',
                'It works for 30 minutes. If you did not ask for it, you can ignore this email.',
            ], link, 'Log in')
        # same answer whether or not the email exists, so addresses can't be probed
        return render(request, 'connect/login_sent.html', {
            'email': form.cleaned_data['email'], 'console_email': 'console' in settings.EMAIL_BACKEND,
        })
    return render(request, 'connect/login.html', {'form': form, 'next': next_url})


def login_link(request, token):
    mentor = read_login_token(token)
    if not mentor:
        messages.error(request, 'That login link has expired or is invalid. Request a new one below.')
        return redirect('connect:login')
    login_mentor(request, mentor)
    messages.success(request, f'Welcome back, {mentor.name}!')
    next_url = request.GET.get('next', '')
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('connect:dashboard')


@require_POST
def logout_view(request):
    logout_mentor(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home:home')


# --------------------------------------------------------------------------
# Mentor dashboard & profile
# --------------------------------------------------------------------------

@mentor_required
def dashboard(request):
    mentor = current_mentor(request)
    bookings = mentor.bookings.all()
    today = timezone.localdate()
    projects = (
        Project.objects.filter(posted_by=mentor).prefetch_related('comments').order_by('-id')
    )
    return render(request, 'connect/dashboard.html', {
        'mentor': mentor,
        'stats': mentor_stats(mentor),
        'pending': bookings.filter(status=Booking.PENDING).order_by('date', 'start_time'),
        'upcoming': bookings.filter(status=Booking.ACCEPTED).order_by('date', 'start_time'),
        'past': bookings.filter(status__in=[Booking.COMPLETED, Booking.DECLINED, Booking.CANCELLED])[:10],
        'projects': projects,
        'today': today,
    })


@mentor_required
def profile_edit(request):
    mentor = current_mentor(request)
    form = MentorProfileForm(request.POST or None, request.FILES or None, instance=mentor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your profile has been updated.')
        return redirect('connect:dashboard')
    return render(request, 'connect/profile_edit.html', {'form': form, 'mentor': mentor})


# --------------------------------------------------------------------------
# Booking a mentor (visitor side, no account: private link per booking)
# --------------------------------------------------------------------------

@require_GET
def slots(request, mentor_id):
    mentor = get_object_or_404(Mentors, pk=mentor_id, status=True)
    try:
        day = date_cls.fromisoformat(request.GET.get('date', ''))
    except ValueError:
        return JsonResponse({'slots': []})
    return JsonResponse({
        'slots': [{'value': t.strftime('%H:%M'), 'label': t.strftime('%I:%M %p').lstrip('0')}
                  for t in slots_for(mentor, day)],
    })


@require_POST
def book(request, mentor_id):
    from mentor.views import MentorDetailView  # re-render the profile with errors

    mentor = get_object_or_404(Mentors, pk=mentor_id, status=True)
    form = BookingForm(request.POST, mentor=mentor)
    with transaction.atomic():
        if not form.is_valid():
            view = MentorDetailView()
            view.setup(request, slug=mentor.slug)
            view.object = mentor
            return view.render_to_response(view.get_context_data(booking_form=form), status=400)
        booking = form.save()

    client_url = reverse('connect:booking_client', args=[booking.token])
    notify.email(request, booking.email, f'Request sent to {mentor.name}', [
        f'Hi {booking.mentee_name},', '',
        f'Your {booking.get_kind_display().lower()} request with {mentor.name} ({booking.when}) has been sent.',
        'You will get an email when they reply. Keep this link: it is your private page for this booking,',
        'where you can chat with the mentor, cancel, or leave a review later.',
    ], client_url, 'Your booking')
    notify.email(request, [mentor.email, settings.SITE_NOTIFY_EMAIL], f'New request from {booking.mentee_name}', [
        f'{booking.mentee_name} would like a {booking.get_kind_display().lower()}: {booking.when}', '',
        booking.requirement, '', 'Accept or decline it from your dashboard.',
    ], reverse('connect:booking_mentor', args=[booking.pk]), 'Open request')

    messages.success(request, f'Request sent! {mentor.name} will reply soon. We emailed you a link to this page.')
    return redirect(client_url)


def booking_client(request, token):
    booking = get_object_or_404(Booking.objects.select_related('mentor'), token=token)
    shows_contact = booking.status in (Booking.ACCEPTED, Booking.COMPLETED)
    return render(request, 'connect/booking_client.html', {
        'booking': booking,
        'mentor': booking.mentor,
        'whatsapp': booking.mentor.whatsapp_number if shows_contact else '',
        'review_form': ReviewForm() if booking.can_review else None,
        'chat_url': reverse('connect:chat_booking_client', args=[booking.token]),
    })


@require_POST
def booking_client_cancel(request, token):
    booking = get_object_or_404(Booking, token=token)
    if booking.status in Booking.ACTIVE:
        booking.status = Booking.CANCELLED
        booking.save(update_fields=['status'])
        notify.email(request, booking.mentor.email, f'{booking.mentee_name} cancelled', [
            f'{booking.mentee_name} cancelled their request for {booking.when}.',
        ], reverse('connect:dashboard'), 'Dashboard')
        messages.success(request, 'Your booking has been cancelled.')
    return redirect('connect:booking_client', token=token)


@require_POST
def booking_client_review(request, token):
    booking = get_object_or_404(Booking.objects.select_related('mentor'), token=token)
    if not booking.can_review:
        raise Http404
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.mentor = booking.mentor
        review.booking = booking
        review.reviewer_name = booking.mentee_name
        review.save()
        messages.success(request, 'Thank you for your review!')
    else:
        messages.error(request, 'Please choose a star rating.')
    return redirect('connect:booking_client', token=token)


# --------------------------------------------------------------------------
# Bookings (mentor side)
# --------------------------------------------------------------------------

def _own_booking(request, pk):
    return get_object_or_404(Booking, pk=pk, mentor=current_mentor(request))


@mentor_required
def booking_mentor(request, pk):
    booking = _own_booking(request, pk)
    return render(request, 'connect/booking_mentor.html', {
        'booking': booking,
        'whatsapp': whatsapp_number(booking.contact_number) if booking.status in (Booking.ACCEPTED, Booking.COMPLETED) else '',
        'chat_url': reverse('connect:chat_booking_mentor', args=[booking.pk]),
    })


BOOKING_TRANSITIONS = {
    # action: (allowed from, new status, email subject, email line)
    'accept': (Booking.PENDING, Booking.ACCEPTED, '{mentor} accepted your request',
               '{mentor} accepted your request for {when}. You can now chat or message them on WhatsApp from your booking page.'),
    'decline': (Booking.PENDING, Booking.DECLINED, '{mentor} can\'t take your request',
                '{mentor} is unable to take your request for {when}. You can book another mentor any time.'),
    'complete': (Booking.ACCEPTED, Booking.COMPLETED, 'How was your session with {mentor}?',
                 'Your session with {mentor} is marked as done. Please take a moment to rate it: it helps other people choose.'),
    'cancel': (Booking.ACCEPTED, Booking.CANCELLED, '{mentor} cancelled your booking',
               '{mentor} had to cancel your booking for {when}. Sorry about that! You can book again from their profile.'),
}


@require_POST
@mentor_required
def booking_mentor_action(request, pk, action):
    booking = _own_booking(request, pk)
    if action not in BOOKING_TRANSITIONS:
        raise Http404
    allowed_from, new_status, subject, line = BOOKING_TRANSITIONS[action]
    if booking.status != allowed_from:
        messages.error(request, 'This request has already been updated.')
        return redirect('connect:booking_mentor', pk=pk)

    booking.status = new_status
    if action in ('accept', 'decline'):
        booking.responded_at = timezone.now()
    booking.save()

    names = {'mentor': booking.mentor.name, 'when': booking.when}
    notify.email(request, booking.email, subject.format(**names), [
        f'Hi {booking.mentee_name},', '', line.format(**names),
    ], reverse('connect:booking_client', args=[booking.token]), 'Your booking')
    messages.success(request, f'Booking {booking.get_status_display().lower()}.')
    return redirect('connect:booking_mentor', pk=pk)


# --------------------------------------------------------------------------
# Projects & proposals (owner side)
# --------------------------------------------------------------------------

def _own_project(request, pk):
    return get_object_or_404(Project, pk=pk, posted_by=current_mentor(request))


@mentor_required
def project_manage(request, pk):
    project = _own_project(request, pk)
    return render(request, 'connect/project_manage.html', {
        'project': project,
        'proposals': project.comments.order_by('state', '-date_added'),
        'milestones': project.milestones.all(),
        'milestone_form': MilestoneForm(),
    })


@mentor_required
def proposal_owner(request, pk):
    proposal = get_object_or_404(Comment.objects.select_related('post'), pk=pk, post__posted_by=current_mentor(request))
    return render(request, 'connect/proposal_owner.html', {
        'proposal': proposal,
        'project': proposal.post,
        'whatsapp': whatsapp_number(proposal.phone_number) if proposal.state == Comment.ACCEPTED else '',
        'chat_url': reverse('connect:chat_proposal_owner', args=[proposal.pk]),
    })


@require_POST
@mentor_required
def proposal_action(request, pk, action):
    proposal = get_object_or_404(Comment.objects.select_related('post'), pk=pk, post__posted_by=current_mentor(request))
    project = proposal.post
    if action not in ('accept', 'decline') or proposal.state != Comment.PENDING:
        messages.error(request, 'This proposal has already been answered.')
        return redirect('connect:proposal_owner', pk=pk)

    if action == 'decline':
        _decline_proposal(request, proposal)
        messages.success(request, 'Proposal declined.')
        return redirect('connect:project_manage', pk=project.pk)

    with transaction.atomic():
        proposal.state = Comment.ACCEPTED
        proposal.save(update_fields=['state'])
        project.stage = Project.STAGE_IN_PROGRESS
        project.save(update_fields=['stage'])
        others = list(project.comments.filter(state=Comment.PENDING))
    for other in others:
        _decline_proposal(request, other)

    notify.email(request, proposal.email, f'Your proposal for "{project.project_name}" was accepted', [
        f'Hi {proposal.name},', '',
        f'{project.posted_by.name} accepted your proposal. Open your proposal page to chat,',
        'see milestones and get their WhatsApp contact.',
    ], reverse('connect:proposal_client', args=[proposal.token]), 'Your proposal')
    messages.success(request, f'You accepted {proposal.name}\'s proposal. The project is now in progress.')
    return redirect('connect:project_manage', pk=project.pk)


def _decline_proposal(request, proposal):
    proposal.state = Comment.DECLINED
    proposal.save(update_fields=['state'])
    notify.email(request, proposal.email, f'Update on "{proposal.post.project_name}"', [
        f'Hi {proposal.name},', '', 'Thank you for your proposal. The project owner has chosen to go another way this time.',
    ])


@require_POST
@mentor_required
def project_close(request, pk):
    project = _own_project(request, pk)
    project.stage = Project.STAGE_CLOSED
    project.save(update_fields=['stage'])
    accepted = project.accepted_proposal
    if accepted:
        notify.email(request, accepted.email, f'"{project.project_name}" is complete', [
            f'Hi {accepted.name},', '',
            f'{project.posted_by.name} has closed the project. Please rate working with them.',
        ], reverse('connect:proposal_client', args=[accepted.token]), 'Leave a review')
    messages.success(request, 'Project closed.')
    return redirect('connect:project_manage', pk=pk)


@require_POST
@mentor_required
def milestone_add(request, pk):
    project = _own_project(request, pk)
    form = MilestoneForm(request.POST)
    if form.is_valid():
        milestone = form.save(commit=False)
        milestone.project = project
        milestone.save()
    else:
        messages.error(request, 'Give the milestone a title.')
    return redirect(f"{reverse('connect:project_manage', args=[pk])}#milestones")


@require_POST
@mentor_required
def milestone_update(request, pk, action):
    milestone = get_object_or_404(Milestone, pk=pk, project__posted_by=current_mentor(request))
    if action == 'toggle':
        milestone.done = not milestone.done
        milestone.save(update_fields=['done'])
    elif action == 'delete':
        milestone.delete()
    return redirect(f"{reverse('connect:project_manage', args=[milestone.project_id])}#milestones")


@require_POST
@mentor_required
def invite(request, mentor_id):
    owner = current_mentor(request)
    invitee = get_object_or_404(Mentors, pk=mentor_id, status=True)
    form = InviteForm(request.POST, projects=Project.objects.filter(
        posted_by=owner, status=True, stage=Project.STAGE_OPEN))
    if form.is_valid():
        project = form.cleaned_data['project']
        lines = [f'Hi {invitee.name},', '', f'{owner.name} invited you to send a proposal for "{project.project_name}".']
        if form.cleaned_data['note']:
            lines += ['', f'Their note: {form.cleaned_data["note"]}']
        notify.email(request, invitee.email, f'{owner.name} invited you to a project', lines,
                     reverse('localproj:project_details', args=[project.pk]), 'View the project')
        messages.success(request, f'Invitation sent to {invitee.name}.')
    return redirect(invitee)


# --------------------------------------------------------------------------
# Proposal page for the proposer (no account: private link)
# --------------------------------------------------------------------------

def proposal_client(request, token):
    proposal = get_object_or_404(Comment.objects.select_related('post__posted_by'), token=token)
    project = proposal.post
    accepted = proposal.state == Comment.ACCEPTED
    can_review = accepted and project.stage == Project.STAGE_CLOSED and not hasattr(proposal, 'review')
    return render(request, 'connect/proposal_client.html', {
        'proposal': proposal,
        'project': project,
        'owner': project.posted_by,
        'whatsapp': project.posted_by.whatsapp_number if accepted else '',
        'milestones': project.milestones.all() if accepted else [],
        'review_form': ReviewForm() if can_review else None,
        'chat_url': reverse('connect:chat_proposal_client', args=[proposal.token]),
    })


@require_POST
def proposal_client_review(request, token):
    proposal = get_object_or_404(Comment.objects.select_related('post__posted_by'), token=token)
    project = proposal.post
    if proposal.state != Comment.ACCEPTED or project.stage != Project.STAGE_CLOSED or hasattr(proposal, 'review'):
        raise Http404
    form = ReviewForm(request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.mentor = project.posted_by
        review.proposal = proposal
        review.reviewer_name = proposal.name
        review.save()
        messages.success(request, 'Thank you for your review!')
    else:
        messages.error(request, 'Please choose a star rating.')
    return redirect('connect:proposal_client', token=token)


# --------------------------------------------------------------------------
# Chat (JSON; polled by script.js). Each thread: mentor side + client side.
# --------------------------------------------------------------------------

def _thread_context(request, kind, ref):
    """
    Resolve a chat thread from the URL and work out who is asking. Returns
    (filter kwargs, my role, open?, other side's email, link the other side should open, my display name).
    """
    if kind == 'booking-client':
        booking = get_object_or_404(Booking.objects.select_related('mentor'), token=ref)
        return ({'booking': booking}, Message.CLIENT, booking.can_chat, booking.mentor.email,
                reverse('connect:booking_mentor', args=[booking.pk]), booking.mentee_name)
    if kind == 'booking-mentor':
        booking = get_object_or_404(Booking, pk=ref, mentor=current_mentor(request))
        return ({'booking': booking}, Message.MENTOR, booking.can_chat, booking.email,
                reverse('connect:booking_client', args=[booking.token]), booking.mentor.name)
    if kind == 'proposal-client':
        proposal = get_object_or_404(Comment.objects.select_related('post__posted_by'), token=ref)
        return ({'proposal': proposal}, Message.CLIENT, proposal.state != Comment.DECLINED,
                proposal.post.posted_by.email, reverse('connect:proposal_owner', args=[proposal.pk]), proposal.name)
    if kind == 'proposal-owner':
        proposal = get_object_or_404(Comment.objects.select_related('post__posted_by'), pk=ref,
                                     post__posted_by=current_mentor(request))
        return ({'proposal': proposal}, Message.MENTOR, proposal.state != Comment.DECLINED, proposal.email,
                reverse('connect:proposal_client', args=[proposal.token]), proposal.post.posted_by.name)
    raise Http404


def chat(request, kind, ref):
    if kind.endswith(('mentor', 'owner')) and not current_mentor(request):
        return JsonResponse({'error': 'login required'}, status=403)
    thread, me, is_open, other_email, other_link, my_name = _thread_context(request, kind, ref)
    thread_messages = Message.objects.filter(**thread)

    if request.method == 'POST':
        if not is_open:
            return JsonResponse({'error': 'This conversation is closed.'}, status=400)
        form = MessageForm(request.POST)
        if not form.is_valid() or not form.cleaned_data['body'].strip():
            return JsonResponse({'error': 'Write a message first.'}, status=400)
        message = Message.objects.create(sender=me, body=form.cleaned_data['body'].strip(), **thread)
        if notify.should_notify_about_message(thread_messages, me):
            notify.email(request, other_email, f'New message from {my_name}', [
                f'{my_name} wrote:', '', message.body,
            ], other_link, 'Reply')

    try:
        after = int(request.GET.get('after', 0))
    except ValueError:
        after = 0
    return JsonResponse({
        'open': is_open,
        'messages': [
            {'id': m.id, 'mine': m.sender == me, 'body': m.body,
             'time': timezone.localtime(m.created_at).strftime('%d %b, %I:%M %p')}
            for m in thread_messages.filter(id__gt=after)
        ],
    })
