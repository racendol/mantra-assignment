from django.http import JsonResponse

import logging

from ratelimit.exceptions import RateLimitExceeded
from ratelimit.services import RateLimitService

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit_service = RateLimitService()

    def __call__(self, request):
        client_ip = self._get_client_ip(request)

        try:
            self.rate_limit_service.check_rate_limit(client_ip)
        except RateLimitExceeded:
            return JsonResponse(
                {"detail": "Rate limit exceeded"},
                status=429,
            )

        return self.get_response(request)

    def _get_client_ip(self, request):
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")

        if forwarded:
            return forwarded.split(",")[0].strip()

        return request.META.get("REMOTE_ADDR")
