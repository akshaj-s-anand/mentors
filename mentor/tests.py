from datetime import date

from django.test import TestCase
from django.urls import reverse

from mentor.models import Mentors


def make_mentor(**kwargs):
    defaults = {
        'name': 'Test Mentor',
        'contact': '9999999999',
        'email': 'mentor@example.com',
        'date_of_birth': date(1990, 1, 1),
        'experience': 5,
        'locality': 'kannur',
        'status': True,
    }
    defaults.update(kwargs)
    return Mentors.objects.create(**defaults)


class MentorVisibilityTests(TestCase):
    def test_list_shows_only_approved_mentors(self):
        make_mentor(name='Approved')
        make_mentor(name='Pending', status=False)
        response = self.client.get(reverse('mentor:all_mentor'))
        self.assertContains(response, 'Approved')
        self.assertNotContains(response, 'Pending')

    def test_unapproved_mentor_detail_is_404(self):
        mentor = make_mentor(status=False)
        response = self.client.get(mentor.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_list_is_paginated_and_keeps_filters(self):
        for i in range(13):
            make_mentor(name=f'Mentor {i}')
        response = self.client.get(reverse('mentor:all_mentor'), {'location': 'kannur'})
        self.assertEqual(len(response.context['mentors']), 12)
        self.assertContains(response, 'location=kannur&amp;page=2')

    def test_ajax_request_returns_only_the_results_fragment(self):
        for i in range(13):
            make_mentor(name=f'Mentor {i}')
        url = reverse('mentor:all_mentor')
        response = self.client.get(url, {'page': 2}, headers={'x-requested-with': 'XMLHttpRequest'})
        self.assertTemplateUsed(response, 'partials/mentor_results.html')
        self.assertTemplateNotUsed(response, 'base.html')
        self.assertNotContains(response, '<html')
        # only page 2's single card, to be appended to the grid
        self.assertEqual(len(response.context['mentors']), 1)
        self.assertContains(response, 'Showing <strong>13</strong> of <strong>13</strong> mentors')
        self.assertContains(response, "reached the end")
        self.assertIn('X-Requested-With', response['Vary'])

        # the same URL without the header is the full page with everything up to page 2,
        # so a reload or the Back button keeps every card that had been scrolled in
        full = self.client.get(url, {'page': 2})
        self.assertTemplateUsed(full, 'base.html')
        self.assertEqual(len(full.context['mentors']), 13)
        self.assertIn('X-Requested-With', full['Vary'])

    def test_bad_category_filter_does_not_crash(self):
        response = self.client.get(reverse('mentor:all_mentor'), {'category': 'abc'})
        self.assertEqual(response.status_code, 200)

    def test_profile_url_uses_the_name(self):
        mentor = make_mentor(name='Jijau Kore')
        twin = make_mentor(name='Jijau Kore')
        reserved = make_mentor(name='Create')
        self.assertEqual(mentor.get_absolute_url(), '/mentor/jijau-kore/')
        self.assertEqual(twin.get_absolute_url(), '/mentor/jijau-kore-2/')
        self.assertEqual(reserved.slug, 'create-mentor')  # can't shadow /mentor/create/
        self.assertContains(self.client.get('/mentor/jijau-kore/'), 'Jijau Kore')

        # renaming keeps the link that was already shared
        mentor.name = 'Jijau K'
        mentor.save()
        self.assertEqual(mentor.get_absolute_url(), '/mentor/jijau-kore/')

    def test_old_numeric_links_redirect_permanently(self):
        mentor = make_mentor(name='Jijau Kore')
        response = self.client.get(f'/mentor/mentors/{mentor.pk}/')
        self.assertRedirects(response, '/mentor/jijau-kore/', status_code=301)

    def test_location_is_shown_capitalised_and_empty_fields_hidden(self):
        mentor = make_mentor(locality='kannur', start_weekday=None, end_weekday=None)
        response = self.client.get(mentor.get_absolute_url())
        self.assertContains(response, 'Kannur')
        self.assertNotContains(response, 'kannur<')
        self.assertNotContains(response, 'None')
        self.assertNotContains(response, 'midnight')
        self.assertNotContains(response, 'href="#"')

    def test_detail_page_does_not_expose_mentor_phone(self):
        mentor = make_mentor(contact='9876543210')
        response = self.client.get(mentor.get_absolute_url())
        self.assertNotContains(response, '9876543210')

