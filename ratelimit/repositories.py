from datetime import timedelta

from django.db import IntegrityError, transaction

from ratelimit.models import RequestLog


class RequestLogRepository:
    @transaction.atomic
    def consume_request(
        self,
        client_ip: str,
        now,
        max_requests: int,
        window_seconds: int,
    ) -> bool:
        request_log, created = self._get_or_create_locked(client_ip, now)

        if not created and now - request_log.created_at > timedelta(
            seconds=window_seconds
        ):
            request_log.counter = 0
            request_log.created_at = now

        if request_log.counter >= max_requests:
            return False

        request_log.counter += 1
        request_log.save(update_fields=["counter", "created_at"])

        return True
    
    def _get_or_create_locked(self, client_ip: str, now):
        # lock row with select for update
        try:
            return (
                RequestLog.objects.select_for_update().get(client_ip=client_ip),
                False,
            )
        except RequestLog.DoesNotExist:
            try:
                with transaction.atomic():
                    return (
                        RequestLog.objects.create(
                            client_ip=client_ip,
                            counter=0,
                            created_at=now,
                        ),
                        True,
                    )
            except IntegrityError:
                return (
                    RequestLog.objects.select_for_update().get(client_ip=client_ip),
                    False,
                )
