from datetime import timedelta
from collections import defaultdict
from threading import Lock

from django.db import transaction
from django.utils import timezone
from django.conf import settings

from ratelimit.exceptions import RateLimitExceeded
from ratelimit.models import RequestLog


class RateLimitService:
    _locks: dict[str, Lock] = defaultdict(Lock)

    @transaction.atomic
    def check_rate_limit(self, client_ip: str) -> None:
        with self._acquire_ip_lock(client_ip):
            now = timezone.now()
            obj, created = RequestLog.objects.get_or_create(
                client_ip=client_ip,
                defaults={
                    "counter": 0,
                    "created_at": now,
                },
            )

            if not created:
                if now - obj.created_at > timedelta(
                    seconds=settings.RATE_LIMIT_WINDOW_SECONDS
                ):
                    obj.counter = 0
                    obj.created_at = now

                if obj.counter >= settings.RATE_LIMIT_REQUESTS:
                    raise RateLimitExceeded()

            obj.counter += 1
            obj.save()

    def _acquire_ip_lock(self, client_ip: str) -> Lock:
        return self._locks[client_ip]
