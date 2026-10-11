from connect.auth import current_mentor


def mentor(request):
    """Exposes the logged-in mentor (or None) to every template, e.g. for the nav bar."""
    return {'current_mentor': current_mentor(request)}
