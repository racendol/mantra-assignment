from django.utils import timezone
from django.conf import settings

from ratelimit.exceptions import RateLimitExceeded
from ratelimit.repositories import RequestLogRepository


class RateLimitService:

    def __init__(self, repository: RequestLogRepository | None = None):
        self.repository = repository or RequestLogRepository()

    def check_rate_limit(self, client_ip: str) -> None:
        now = timezone.now()
        is_allowed = self.repository.consume_request(
            client_ip=client_ip,
            now=now,
            max_requests=settings.RATE_LIMIT_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        )

        if not is_allowed:
            raise RateLimitExceeded("Rate Limit Exceeded")
