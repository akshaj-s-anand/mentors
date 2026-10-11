"""
Passwordless login for mentors: they enter their email and get a login link (valid 30 minutes).

The logged-in mentor's id lives in the session; no Django User is needed, so all
existing mentors can log in straight away with the email already on their profile.
"""
from functools import wraps

from django.contrib import messages
from django.core import signing
from django.shortcuts import redirect
from django.urls import reverse

from mentor.models import Mentors

SESSION_KEY = 'mentor_id'
LINK_MAX_AGE = 30 * 60  # seconds
_SALT = 'connect.login-link'


def make_login_token(mentor):
    # signed with SECRET_KEY and timestamped: valid for LINK_MAX_AGE, can't be forged or edited
    return signing.dumps({'id': mentor.pk}, salt=_SALT)


def read_login_token(token):
    """Return the mentor for a valid, unexpired link, else None."""
    try:
        data = signing.loads(token, salt=_SALT, max_age=LINK_MAX_AGE)
    except signing.BadSignature:  # includes SignatureExpired
        return None
    return Mentors.objects.filter(pk=data.get('id'), status=True).first()


def login_mentor(request, mentor):
    request.session.cycle_key()  # new session id on login
    request.session[SESSION_KEY] = mentor.pk


def logout_mentor(request):
    request.session.flush()


def current_mentor(request):
    if not hasattr(request, '_current_mentor'):
        mentor_id = request.session.get(SESSION_KEY)
        request._current_mentor = (
            Mentors.objects.filter(pk=mentor_id, status=True).first() if mentor_id else None
        )
    return request._current_mentor


def mentor_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not current_mentor(request):
            messages.info(request, 'Log in with your mentor email to continue.')
            return redirect(f"{reverse('connect:login')}?next={request.get_full_path()}")
        return view(request, *args, **kwargs)
    return wrapper
