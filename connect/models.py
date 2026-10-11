import uuid
from datetime import datetime, timedelta
from statistics import median

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, FloatField, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce
from django.utils import timezone

from localproj.models import Comment
from mentor.models import Mentors


class Booking(models.Model):
    """A request from a visitor (mentee) for a call with a mentor."""

    PENDING, ACCEPTED, DECLINED, COMPLETED, CANCELLED = 'pending', 'accepted', 'declined', 'completed', 'cancelled'
    STATUS_CHOICES = (
        (PENDING, 'Waiting for the mentor'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
        (COMPLETED, 'Completed'),
        (CANCELLED, 'Cancelled'),
    )
    # statuses that hold a time slot / allow chatting
    ACTIVE = (PENDING, ACCEPTED)
    OPEN_FOR_CHAT = (PENDING, ACCEPTED, COMPLETED)

    INTRO, SESSION = 'intro', 'session'
    KIND_CHOICES = ((INTRO, 'Free intro call'), (SESSION, 'Mentoring session'))

    mentor = models.ForeignKey(Mentors, on_delete=models.CASCADE, related_name='bookings')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=SESSION)
    mentee_name = models.CharField(max_length=100)
    email = models.EmailField()
    contact_number = models.CharField(max_length=15)
    requirement = models.TextField(max_length=1000)

    # an exact slot when the mentor has set hours, otherwise a preferred date + free-text time
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    preferred_time = models.CharField(max_length=60, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    # private link for the mentee, who has no account
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['mentor', 'date', 'status'])]

    def __str__(self):
        return f'{self.mentee_name} → {self.mentor}'

    @property
    def duration(self):
        return 15 if self.kind == self.INTRO else self.mentor.session_minutes

    @property
    def end_time(self):
        if not self.start_time:
            return None
        return (datetime.combine(self.date, self.start_time) + timedelta(minutes=self.duration)).time()

    @property
    def when(self):
        if self.start_time:
            return f"{self.date:%a %d %b} · {self.start_time:%I:%M %p}".replace(' 0', ' ')
        return f"{self.date:%a %d %b}" + (f" · {self.preferred_time}" if self.preferred_time else '')

    @property
    def can_chat(self):
        return self.status in self.OPEN_FOR_CHAT

    @property
    def can_review(self):
        return self.status == self.COMPLETED and not hasattr(self, 'review')


class Review(models.Model):
    """A rating of a mentor, from a completed booking or a closed project."""

    mentor = models.ForeignKey(Mentors, on_delete=models.CASCADE, related_name='reviews')
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='review')
    proposal = models.OneToOneField(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='review')
    reviewer_name = models.CharField(max_length=100)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=1000, blank=True)
    # admins can hide abusive reviews without deleting them
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rating}★ for {self.mentor} by {self.reviewer_name}'


class Message(models.Model):
    """On-site chat. Every thread has a mentor side and a client side (mentee or proposer)."""

    MENTOR, CLIENT = 'mentor', 'client'
    SENDER_CHOICES = ((MENTOR, 'Mentor'), (CLIENT, 'Client'))

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    proposal = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    sender = models.CharField(max_length=6, choices=SENDER_CHOICES)
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.CheckConstraint(
                condition=Q(booking__isnull=False, proposal__isnull=True) | Q(booking__isnull=True, proposal__isnull=False),
                name='message_belongs_to_one_thread',
            )
        ]

    def __str__(self):
        return f'{self.sender}: {self.body[:40]}'


def mentor_stats(mentor):
    """Trust numbers shown on a mentor's profile."""
    reviews = mentor.reviews.filter(is_public=True).aggregate(avg=Avg('rating'), count=Count('id'))
    completed = mentor.bookings.filter(status=Booking.COMPLETED).count()

    # how long the mentor usually takes to answer a request (last 20 answered)
    waits = [
        (responded - created).total_seconds() / 3600
        for created, responded in mentor.bookings.filter(responded_at__isnull=False)
        .order_by('-created_at').values_list('created_at', 'responded_at')[:20]
    ]
    response_hours = median(waits) if len(waits) >= 2 else None

    return {
        'rating': round(reviews['avg'], 1) if reviews['avg'] else None,
        'review_count': reviews['count'],
        'completed': completed,
        'response_hours': response_hours,
    }


def rating_annotations():
    """Annotations for listing mentors with their rating, without a query per card."""
    public = Review.objects.filter(mentor=OuterRef('pk'), is_public=True).values('mentor')
    return {
        'avg_rating': Subquery(public.annotate(a=Avg('rating')).values('a')[:1], output_field=FloatField()),
        'review_count': Coalesce(
            Subquery(public.annotate(c=Count('id')).values('c')[:1], output_field=IntegerField()), 0
        ),
    }


def slots_for(mentor, day, now=None):
    """Free start times on `day` for a mentor's normal session length."""
    now = now or timezone.localtime()
    if not mentor.has_schedule or day.weekday() not in mentor.weekday_indexes:
        return []
    if day < now.date() or day > now.date() + timedelta(days=60):
        return []

    length = timedelta(minutes=mentor.session_minutes)
    taken = [
        (datetime.combine(day, b.start_time), datetime.combine(day, b.end_time))
        for b in mentor.bookings.filter(date=day, status__in=Booking.ACTIVE, start_time__isnull=False)
    ]
    earliest = (now + timedelta(hours=2)).replace(tzinfo=None)  # leave the mentor time to see the request

    slots = []
    cursor = datetime.combine(day, mentor.time_from)
    end = datetime.combine(day, mentor.time_to)
    while cursor + length <= end:
        overlaps = any(cursor < t_end and cursor + length > t_start for t_start, t_end in taken)
        if cursor >= earliest and not overlaps:
            slots.append(cursor.time())
        cursor += length
    return slots
