import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)


def email(request, to, subject, lines, link_path=None, link_label='Open'):
    """Send a short plain-text email. Failures are logged, never shown to the visitor."""
    recipients = [address for address in ([to] if isinstance(to, str) else to) if address]
    if not recipients:
        return
    body = '\n'.join(lines)
    if link_path:
        body += f'\n\n{link_label}: {request.build_absolute_uri(link_path)}'
    body += '\n\n— Oldscool'
    try:
        send_mail(f'[Oldscool] {subject}', body, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception:
        logger.exception('Could not send "%s" to %s', subject, recipients)


def should_notify_about_message(thread_messages, sender):
    """Email about a new chat message only if this sender hasn't written in the last 10 minutes."""
    since = timezone.now() - timedelta(minutes=10)
    # the new message is already saved, so more than one recent message means we've notified already
    return thread_messages.filter(sender=sender, created_at__gte=since).count() <= 1
