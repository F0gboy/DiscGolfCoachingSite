from django.conf import settings
from django.shortcuts import redirect


class LoginRequiredMiddleware:
    """Middleware that requires authentication for most site pages.

    Exemptions are based on path prefixes: the LOGIN_URL, registration
    path, admin, and static/media when DEBUG. This avoids fragile view-name
    resolution.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow access if already authenticated
        if request.user.is_authenticated:
            return self.get_response(request)
        path = request.path
        # Always allow access to auth related and admin URLs and the public root
        login_url = settings.LOGIN_URL
        accounts_prefix = '/accounts/'
        admin_prefix = '/admin/'

        if path == '/' or path.startswith(login_url) or path.startswith(accounts_prefix) or path.startswith(admin_prefix):
            return self.get_response(request)

        # Allow static and media in DEBUG
        if settings.DEBUG and (path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL)):
            return self.get_response(request)

        # Otherwise redirect anonymous users to login
        return redirect(settings.LOGIN_URL)
