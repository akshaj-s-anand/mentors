import re
from datetime import time, timedelta

from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from connect.auth import make_login_token
from connect.models import Booking, Message, Review, slots_for
from localproj.models import Comment, Milestone, Project
from mentor.models import Category, Specialization
from mentor.tests import make_mentor


def scheduled_mentor(**kwargs):
    defaults = {'start_weekday': 'monday', 'end_weekday': 'sunday',
                'time_from': time(9, 0), 'time_to': time(17, 0), 'session_minutes': 30}
    defaults.update(kwargs)
    return make_mentor(**defaults)


def next_week():
    return timezone.localdate() + timedelta(days=7)


def booking_data(**kwargs):
    data = {'kind': 'session', 'mentee_name': 'Asha', 'email': 'asha@example.com',
            'contact_number': '9123456789', 'requirement': 'Help with my pitch deck',
            'date': next_week().isoformat(), 'start_time': '10:00'}
    data.update(kwargs)
    return data


class LoginTests(TestCase):
    def test_login_link_logs_the_mentor_in(self):
        mentor = make_mentor(email='mentor@example.com')
        response = self.client.post(reverse('connect:login'), {'email': 'MENTOR@example.com'})
        self.assertContains(response, 'Check your email')
        link = re.search(r'https?://\S+/account/login/\S+/', mail.outbox[0].body).group(0)

        response = self.client.get(link)
        self.assertRedirects(response, reverse('connect:dashboard'))
        self.assertEqual(self.client.session['mentor_id'], mentor.pk)

    def test_unknown_email_gets_the_same_answer_and_no_mail(self):
        response = self.client.post(reverse('connect:login'), {'email': 'nobody@example.com'})
        self.assertContains(response, 'Check your email')
        self.assertEqual(len(mail.outbox), 0)

    def test_unapproved_mentor_cannot_log_in(self):
        mentor = make_mentor(status=False)
        self.client.get(reverse('connect:login_link', args=[make_login_token(mentor)]))
        self.assertNotIn('mentor_id', self.client.session)

    def test_tampered_link_is_rejected(self):
        response = self.client.get(reverse('connect:login_link', args=['not-a-real-token']))
        self.assertRedirects(response, reverse('connect:login'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('connect:dashboard'))
        self.assertRedirects(response, f"{reverse('connect:login')}?next={reverse('connect:dashboard')}")


class SlotTests(TestCase):
    def test_slots_follow_schedule_and_skip_taken_ones(self):
        mentor = scheduled_mentor()
        day = next_week()
        slots = slots_for(mentor, day)
        self.assertEqual(slots[0], time(9, 0))
        self.assertEqual(slots[-1], time(16, 30))
        self.assertEqual(len(slots), 16)

        Booking.objects.create(mentor=mentor, mentee_name='X', email='x@example.com', contact_number='9123456789',
                               requirement='r', date=day, start_time=time(10, 0), status=Booking.ACCEPTED)
        self.assertNotIn(time(10, 0), slots_for(mentor, day))

    def test_wraparound_week_and_no_schedule(self):
        mentor = scheduled_mentor(start_weekday='friday', end_weekday='monday')
        self.assertEqual(mentor.weekday_indexes, [4, 5, 6, 0])
        self.assertFalse(make_mentor().has_schedule)  # 00:00–00:00 like most existing mentors


class BookingFlowTests(TestCase):
    def setUp(self):
        self.mentor = scheduled_mentor(email='mentor@example.com', contact='9876543210')
        self.client.get(reverse('connect:login_link', args=[make_login_token(self.mentor)]))
        self.mentor_client = self.client
        self.visitor = self.client_class()

    def book(self, **kwargs):
        return self.visitor.post(reverse('connect:book', args=[self.mentor.pk]), booking_data(**kwargs))

    def test_full_booking_lifecycle(self):
        response = self.book()
        booking = Booking.objects.get()
        client_url = reverse('connect:booking_client', args=[booking.token])
        self.assertRedirects(response, client_url)
        # mentee gets their private link, mentor (+ site) get the request
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn(client_url, mail.outbox[0].body)

        # phone is private until the mentor accepts
        self.assertNotContains(self.visitor.get(client_url), 'wa.me/919876543210')
        self.mentor_client.post(reverse('connect:booking_mentor_action', args=[booking.pk, 'accept']))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.ACCEPTED)
        self.assertIsNotNone(booking.responded_at)
        self.assertContains(self.visitor.get(client_url), 'wa.me/919876543210')

        # no review before the session is done
        self.visitor.post(reverse('connect:booking_client_review', args=[booking.token]), {'rating': 5})
        self.assertFalse(Review.objects.exists())

        self.mentor_client.post(reverse('connect:booking_mentor_action', args=[booking.pk, 'complete']))
        self.visitor.post(reverse('connect:booking_client_review', args=[booking.token]),
                          {'rating': 4, 'comment': 'Very helpful'})
        review = Review.objects.get()
        self.assertEqual((review.mentor, review.rating, review.reviewer_name), (self.mentor, 4, 'Asha'))

        # one review per booking
        response = self.visitor.post(reverse('connect:booking_client_review', args=[booking.token]), {'rating': 1})
        self.assertEqual(response.status_code, 404)

        # rating shows on the profile and in the list
        self.assertContains(self.visitor.get(self.mentor.get_absolute_url()), 'Very helpful')
        listing = self.visitor.get(reverse('mentor:all_mentor'))
        self.assertEqual(listing.context['mentors'][0].avg_rating, 4.0)

    def test_taken_slot_is_rejected(self):
        self.book()
        response = self.book(mentee_name='Ravi', email='ravi@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertContains(response, 'just taken', status_code=400)
        self.assertEqual(Booking.objects.count(), 1)

    def test_mentor_without_schedule_takes_preferred_time(self):
        mentor = make_mentor(name='No Hours')
        response = self.visitor.post(reverse('connect:book', args=[mentor.pk]),
                                     booking_data(start_time='', preferred_time='evenings'))
        booking = Booking.objects.get(mentor=mentor)
        self.assertRedirects(response, reverse('connect:booking_client', args=[booking.token]))
        self.assertIsNone(booking.start_time)
        self.assertEqual(booking.preferred_time, 'evenings')

    def test_other_mentors_cannot_touch_the_booking(self):
        self.book()
        booking = Booking.objects.get()
        other = make_mentor(name='Other', email='other@example.com')
        intruder = self.client_class()
        intruder.get(reverse('connect:login_link', args=[make_login_token(other)]))
        response = intruder.post(reverse('connect:booking_mentor_action', args=[booking.pk, 'accept']))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(intruder.get(reverse('connect:chat_booking_mentor', args=[booking.pk])).status_code, 404)

    def test_chat_between_mentee_and_mentor(self):
        self.book()
        booking = Booking.objects.get()
        mail.outbox.clear()
        client_chat = reverse('connect:chat_booking_client', args=[booking.token])
        mentor_chat = reverse('connect:chat_booking_mentor', args=[booking.pk])

        self.visitor.post(client_chat, {'body': 'Hello! <script>alert(1)</script>'})
        self.visitor.post(client_chat, {'body': 'Second message'})
        data = self.mentor_client.get(mentor_chat).json()
        self.assertEqual([m['mine'] for m in data['messages']], [False, False])
        # only the first message in a burst emails the other side
        self.assertEqual(len(mail.outbox), 1)

        reply = self.mentor_client.post(f"{mentor_chat}?after={data['messages'][-1]['id']}", {'body': 'Hi Asha'}).json()
        self.assertEqual([m['body'] for m in reply['messages']], ['Hi Asha'])
        self.assertTrue(reply['messages'][0]['mine'])

        # declined → chat closes
        self.mentor_client.post(reverse('connect:booking_mentor_action', args=[booking.pk, 'decline']))
        response = self.visitor.post(client_chat, {'body': 'Still there?'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.count(), 3)

    def test_mentee_can_cancel(self):
        self.book()
        booking = Booking.objects.get()
        self.visitor.post(reverse('connect:booking_client_cancel', args=[booking.token]))
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.CANCELLED)
        # the slot is free again
        self.assertIn(time(10, 0), slots_for(self.mentor, next_week()))


class ProjectFlowTests(TestCase):
    def setUp(self):
        self.owner = make_mentor(email='owner@example.com', contact='9876543210')
        self.client.get(reverse('connect:login_link', args=[make_login_token(self.owner)]))
        self.visitor = self.client_class()

    def test_posting_requires_login_and_sets_owner(self):
        create_url = reverse('localproj:create_project')
        self.assertEqual(self.visitor.get(create_url).status_code, 302)

        other = make_mentor(name='Someone else')
        self.client.post(create_url, {
            'project_name': 'Brand new idea', 'description': 'Logo for a bakery',
            'location': 'Kannur', 'budget': '₹5,000', 'posted_by': other.pk,
        })
        project = Project.objects.get()
        self.assertEqual(project.posted_by, self.owner)  # can't post as someone else
        self.assertEqual(project.project_name, 'Brand new idea')  # free text, not a dropdown
        self.assertFalse(project.status)  # still needs admin approval

    def test_proposal_lifecycle(self):
        project = Project.objects.create(project_name='Website', location='Kannur', posted_by=self.owner,
                                         status=True, description='Need a site')
        propose = reverse('localproj:add_comment', args=[project.pk])
        proposal_data = {'name': 'Ravi', 'phone_number': '9123456789', 'email': 'ravi@example.com',
                         'response': 'I can build it', 'proposed_price': '₹10,000', 'timeline': '2 weeks'}
        self.visitor.post(propose, proposal_data)
        self.visitor.post(propose, {**proposal_data, 'name': 'Meera', 'email': 'meera@example.com'})
        ravi, meera = Comment.objects.order_by('pk')
        ravi_url = reverse('connect:proposal_client', args=[ravi.token])
        self.assertNotContains(self.visitor.get(ravi_url), 'wa.me/919876543210')

        self.client.post(reverse('connect:proposal_action', args=[ravi.pk, 'accept']))
        ravi.refresh_from_db(); meera.refresh_from_db(); project.refresh_from_db()
        self.assertEqual((ravi.state, meera.state, project.stage),
                         (Comment.ACCEPTED, Comment.DECLINED, Project.STAGE_IN_PROGRESS))
        self.assertContains(self.visitor.get(ravi_url), 'wa.me/919876543210')

        # project no longer takes proposals
        self.visitor.post(propose, {**proposal_data, 'name': 'Late'})
        self.assertEqual(Comment.objects.count(), 2)

        # milestones are visible to the hired person
        self.client.post(reverse('connect:milestone_add', args=[project.pk]), {'title': 'Homepage draft'})
        milestone = Milestone.objects.get()
        self.client.post(reverse('connect:milestone_update', args=[milestone.pk, 'toggle']))
        milestone.refresh_from_db()
        self.assertTrue(milestone.done)
        self.assertContains(self.visitor.get(ravi_url), 'Homepage draft')

        # chat both ways
        self.visitor.post(reverse('connect:chat_proposal_client', args=[ravi.token]), {'body': 'Started!'})
        data = self.client.get(reverse('connect:chat_proposal_owner', args=[ravi.pk])).json()
        self.assertEqual(data['messages'][0]['body'], 'Started!')

        # closing lets the hired person review the owner
        self.client.post(reverse('connect:project_close', args=[project.pk]))
        self.visitor.post(reverse('connect:proposal_client_review', args=[ravi.token]), {'rating': 5})
        self.assertEqual(Review.objects.get().mentor, self.owner)

    def test_owner_pages_are_private(self):
        project = Project.objects.create(project_name='Mine', location='Kannur', posted_by=self.owner, status=True)
        other = make_mentor(name='Other')
        intruder = self.client_class()
        intruder.get(reverse('connect:login_link', args=[make_login_token(other)]))
        self.assertEqual(intruder.get(reverse('connect:project_manage', args=[project.pk])).status_code, 404)


class DiscoveryTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Design')
        self.logo = Specialization.objects.create(category=category, specialist='Logo Design')
        self.designer = make_mentor(name='Designer', headline='Brand designer', locality='kannur', verified=True)
        self.designer.specializations.add(self.logo)
        make_mentor(name='Accountant', about='GST and taxes', locality='kozhikode')

    def names(self, response):
        return [m.name for m in response.context['mentors']]

    def test_keyword_search(self):
        url = reverse('mentor:all_mentor')
        self.assertEqual(self.names(self.client.get(url, {'q': 'logo'})), ['Designer'])
        self.assertEqual(self.names(self.client.get(url, {'q': 'gst'})), ['Accountant'])

    def test_skill_and_district_pages(self):
        response = self.client.get(reverse('mentor:skill', args=[self.logo.pk, 'logo-design']))
        self.assertEqual(self.names(response), ['Designer'])
        self.assertContains(response, 'Logo Design <span class="green-text">mentors</span>', html=False)
        district = self.client.get(reverse('mentor:skill_district', args=[self.logo.pk, 'logo-design', 'kozhikode']))
        self.assertEqual(self.names(district), [])

    def test_card_shows_verified_badge_and_skill_link(self):
        response = self.client.get(reverse('mentor:all_mentor'))
        self.assertContains(response, 'Verified by Oldscool')
        self.assertContains(response, reverse('mentor:skill', args=[self.logo.pk, 'logo-design']))
