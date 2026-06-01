from unittest.mock import patch

import pytest
from concurrent.futures import ThreadPoolExecutor

from django.urls import reverse
from entailment.dto import EntailmentResult
from entailment.enum import EntailmentLabel
from ratelimit.models import RequestLog


@pytest.mark.django_db(transaction=True)
class TestConcurrentWrites:
    def _call_api(self, client, ip: str):
        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
            HTTP_X_FORWARDED_FOR=ip,
        )
        return response

    @patch("judge.views.entailment_service.run_inference")
    def test_6_ips_concurrent_writes(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
        ]

        ips = ["1.1.1." + str(i) for i in range(6)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            tasks = []

            for ip in ips:
                for _ in range(5):
                    tasks.append(
                        executor.submit(
                            self._call_api,
                            client,
                            ip,
                        )
                    )

            responses = [f.result() for f in tasks]

        # all should succeed
        assert all(r.status_code == 200 for r in responses)

        logs = RequestLog.objects.all()

        # db should have all IP entries
        assert logs.count() == len(ips)

        # counter should be 5
        assert all(log.counter == 5 for log in logs)

        saved_ips = set(logs.values_list("client_ip", flat=True))
        assert saved_ips == set(ips)

    @patch("judge.views.entailment_service.run_inference")
    def test_30_ips_concurrent_writes(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
        ]

        ips = ["1.1.1." + str(i) for i in range(30)]

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self._call_api, client, ip) for ip in ips]

            responses = [f.result() for f in futures]

        # all should succeed
        assert all(r.status_code == 200 for r in responses)

        # db should have all IP entries
        logs = RequestLog.objects.all()

        assert logs.count() == len(ips)

        saved_ips = set(logs.values_list("client_ip", flat=True))
        assert saved_ips == set(ips)

    @patch("judge.views.entailment_service.run_inference")
    def test_high_concurrency_1_ip(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
        ]

        ip = "7.7.7.7"

        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(
                executor.map(lambda _: self._call_api(client, ip), range(50))
            )

        statuses = [r.status_code for r in results]

        assert 200 in statuses

        # db should still be consistent
        logs = RequestLog.objects.filter(client_ip=ip)
        assert logs.count() == 1
