from rest_framework.throttling import BaseThrottle

from ratelimit.exceptions import RateLimitExceeded
from ratelimit.services import RateLimitService


class RateLimitThrottle(BaseThrottle):
    def __init__(self):
        self.rate_limit_service = RateLimitService()

    def allow_request(self, request, view):
        client_ip = self.get_ident(request)

        try:
            self.rate_limit_service.check_rate_limit(client_ip)
        except RateLimitExceeded:
            return False

        return True
