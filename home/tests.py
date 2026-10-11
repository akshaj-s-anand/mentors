from django.test import TestCase
from django.urls import reverse

from home.models import Contact
from localproj.models import Project
from mentor.models import Category, Specialization
from mentor.tests import make_mentor


class HomePageTests(TestCase):
    def test_query_count_does_not_grow_with_mentors(self):
        category = Category.objects.create(name='Design')
        spec = Specialization.objects.create(category=category, specialist='UI')
        for i in range(20):
            mentor = make_mentor(name=f'Mentor {i}')
            mentor.specializations.add(spec)
            Project.objects.create(project_name=f'Project {i}', location='Kannur', posted_by=mentor, status=True)

        # mentors, specializations (+category), projects, categories, project names
        with self.assertNumQueries(5):
            response = self.client.get(reverse('home:home'))
        self.assertEqual(len(response.context['mentors']), 8)


class ContactFormTests(TestCase):
    def test_rejects_non_numeric_phone(self):
        response = self.client.post(reverse('home:contact'), {
            'name': 'Asha', 'phone_number': 'abcdefghij', 'message': 'Hello',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Contact.objects.exists())

    def test_accepts_valid_submission(self):
        response = self.client.post(reverse('home:contact'), {
            'name': 'Asha', 'phone_number': '9123456789', 'message': 'Hello',
        })
        self.assertRedirects(response, reverse('home:contact'))
        self.assertTrue(Contact.objects.exists())
