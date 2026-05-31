import pytest

from ratelimit.exceptions import RateLimitExceeded
from ratelimit.services import RateLimitService


@pytest.mark.django_db
class TestRateLimitService:
    def test_allow_requests_within_limit(self):
        service = RateLimitService()

        for _ in range(5):
            service.check_rate_limit("127.0.0.1")

    def test_reject_when_limit_exceeded(self):
        service = RateLimitService()

        for _ in range(5):
            service.check_rate_limit("127.0.0.1")

        with pytest.raises(RateLimitExceeded):
            service.check_rate_limit("127.0.0.1")

    def test_different_ips_are_independent(self):
        service = RateLimitService()

        for _ in range(5):
            service.check_rate_limit("127.0.0.1")

        service.check_rate_limit("127.0.0.2")
