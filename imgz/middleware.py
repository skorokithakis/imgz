import time

from django.utils.deprecation import MiddlewareMixin
from ipware import get_client_ip


class DisableCSRFMiddleware(MiddlewareMixin):
    """CSRF is unnecessary because session cookies use SameSite=Lax by default."""

    def process_request(self, request):
        request._dont_enforce_csrf_checks = True


class StatsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Store the start time when the request comes in."""
        request.start_time = time.time()

    def process_response(self, request, response):
        """Calculate and output the page generation duration."""
        # Get the start time from the request and calculate how long
        # the response took.
        duration = time.time() - request.start_time

        # Add the header.
        response["X-Page-Generation-Duration-ms"] = int(duration * 1000)
        return response


class RealIPMiddleware(MiddlewareMixin):
    """
    Django middleware to get the real ip from the request, update META.
    """

    def process_request(self, request):
        real_ip, _ = get_client_ip(request)
        request.META["REMOTE_ADDR"] = real_ip
        return None
