from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from localproj.admin import approve_projects
from localproj.models import Comment, Project
from mentor.tests import make_mentor


def make_project(mentor, **kwargs):
    defaults = {'project_name': 'Web Design', 'location': 'Kannur', 'posted_by': mentor, 'status': True}
    defaults.update(kwargs)
    return Project.objects.create(**defaults)


class ProjectTests(TestCase):
    def setUp(self):
        self.mentor = make_mentor()

    def test_unapproved_project_is_hidden(self):
        project = make_project(self.mentor, status=False, project_name='Secret Plan')
        self.assertNotContains(self.client.get(reverse('localproj:all_projects')), 'Secret Plan')
        response = self.client.get(reverse('localproj:project_details', args=[project.pk]))
        self.assertEqual(response.status_code, 404)

    def test_invalid_comment_shows_errors(self):
        project = make_project(self.mentor)
        response = self.client.post(reverse('localproj:add_comment', args=[project.pk]), {
            'name': 'Ravi', 'phone_number': '9123456789', 'email': 'not-an-email', 'response': 'Interested',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Comment.objects.exists())
        self.assertContains(response, 'value="Ravi"', status_code=400)

    def test_approve_action_sets_status(self):
        project = make_project(self.mentor, status=False)
        request = RequestFactory().post('/')
        request.user = User.objects.create_superuser('boss', 'boss@example.com', 'pw')
        request._messages = type('M', (), {'add': lambda *a, **k: None})()
        approve_projects(site._registry[Project], request, Project.objects.filter(pk=project.pk))
        project.refresh_from_db()
        self.assertTrue(project.status)
