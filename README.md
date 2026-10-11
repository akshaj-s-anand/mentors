# Oldscool — Local Mentors & Projects

Django site that connects local mentors and professionals with projects in Kerala.

- **home** — landing, about, contact, enrol and terms pages
- **mentor** — mentor registration, directory, profiles and mentee requests
- **localproj** — project posting, directory, proposals and milestones
- **connect** — mentor login by email link, dashboard, bookings with time slots, reviews, on-site chat

Visitors (mentees and people sending proposals) don't need accounts: each booking or proposal has a private link (`/b/<token>/`, `/p/<token>/`) that is emailed to them. Mentors log in at `/account/login/` with the email on their profile.

Mentors and projects stay hidden until an admin approves them (`status`) in `/admin/`.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r req.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

No environment variables are needed locally. Without `EMAIL_HOST_PASSWORD`, emails are printed to the console instead of being sent.

## Tests

```bash
python manage.py test
```

## Production

Set the variables listed in `.env.example` in the server environment (at minimum `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `EMAIL_HOST_PASSWORD`), then:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Serve `staticfiles/` and `media/` from the web server, not from Django.
