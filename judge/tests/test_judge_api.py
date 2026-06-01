import time
from unittest.mock import patch

import pytest

from django.urls import reverse

from entailment.dto import EntailmentResult
from entailment.enum import EntailmentLabel


@pytest.mark.django_db
class TestJudgeView:
    @patch("judge.views.entailment_service.run_inference")
    def test_success(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            )
        ]

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.data["label"] == EntailmentLabel.ENTAILMENT
        assert response.data["score"] == 0.95

    @patch("judge.views.entailment_service.run_inference")
    def test_success_no_entail(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.NO_ENTAILMENT,
                score=0.95,
            )
        ]

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.data["label"] == EntailmentLabel.NO_ENTAILMENT
        assert response.data["score"] == 0.95

    def test_error_validation(self, client):
        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
            },
            content_type="application/json",
        )

        assert response.status_code == 400

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            )
        ]

        for _ in range(5):
            client.post(
                reverse("judge-list"),
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                content_type="application/json",
            )

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
        )

        assert response.status_code == 429

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit_different_ip(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            )
        ]

        for _ in range(5):
            client.post(
                reverse("judge-list"),
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                content_type="application/json",
                HTTP_X_FORWARDED_FOR="1.1.1.1",
            )

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        response2 = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="2.2.2.2",
        )

        assert response.status_code == 429
        assert response2.status_code == 200

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit_reset(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            )
        ]

        for _ in range(5):
            client.post(
                reverse("judge-list"),
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                content_type="application/json",
                HTTP_X_FORWARDED_FOR="1.1.1.1",
            )

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        assert response.status_code == 429

        time.sleep(1)

        response = client.post(
            reverse("judge-list"),
            {
                "sentence1": "A",
                "sentence2": "B",
            },
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestBulkJudgeView:
    @patch("judge.views.entailment_service.run_inference")
    def test_success(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
            EntailmentResult(
                label=EntailmentLabel.NO_ENTAILMENT,
                score=0.82,
            ),
        ]

        response = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_bulk_over_limit(self, client):
        payload = [
            {
                "sentence1": f"P{i}",
                "sentence2": f"H{i}",
            }
            for i in range(101)
        ]

        response = client.post(
            reverse("judge-bulk"),
            payload,
            content_type="application/json",
        )

        assert response.status_code == 400

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
            EntailmentResult(
                label=EntailmentLabel.NO_ENTAILMENT,
                score=0.82,
            ),
        ]

        for _ in range(5):
            client.post(
                reverse("judge-bulk"),
                [
                    {
                        "sentence1": "A",
                        "sentence2": "B",
                    },
                    {
                        "sentence1": "C",
                        "sentence2": "D",
                    },
                ],
                content_type="application/json",
            )

        response = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
        )

        assert response.status_code == 429

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit_different_ip(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
            EntailmentResult(
                label=EntailmentLabel.NO_ENTAILMENT,
                score=0.82,
            ),
        ]

        for _ in range(5):
            client.post(
                reverse("judge-bulk"),
                [
                    {
                        "sentence1": "A",
                        "sentence2": "B",
                    },
                    {
                        "sentence1": "C",
                        "sentence2": "D",
                    },
                ],
                content_type="application/json",
                HTTP_X_FORWARDED_FOR="1.1.1.1",
            )

        response = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        response2 = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="2.2.2.2",
        )

        assert response.status_code == 429
        assert response2.status_code == 200

    @patch("judge.views.entailment_service.run_inference")
    def test_error_rate_limit_reset(self, mock_run, client):
        mock_run.return_value = [
            EntailmentResult(
                label=EntailmentLabel.ENTAILMENT,
                score=0.95,
            ),
            EntailmentResult(
                label=EntailmentLabel.NO_ENTAILMENT,
                score=0.82,
            ),
        ]

        for _ in range(5):
            client.post(
                reverse("judge-bulk"),
                [
                    {
                        "sentence1": "A",
                        "sentence2": "B",
                    },
                    {
                        "sentence1": "C",
                        "sentence2": "D",
                    },
                ],
                content_type="application/json",
                HTTP_X_FORWARDED_FOR="1.1.1.1",
            )

        response = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        assert response.status_code == 429

        time.sleep(1)

        response = client.post(
            reverse("judge-bulk"),
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
            HTTP_X_FORWARDED_FOR="1.1.1.1",
        )

        assert response.status_code == 200


@pytest.mark.django_db
class TestNotFound:
    def test_notfound(self, client):
        response = client.post(
            "/notfound",
            [
                {
                    "sentence1": "A",
                    "sentence2": "B",
                },
                {
                    "sentence1": "C",
                    "sentence2": "D",
                },
            ],
            content_type="application/json",
        )

        assert response.status_code == 404
