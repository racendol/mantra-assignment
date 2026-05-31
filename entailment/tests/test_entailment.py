from unittest.mock import Mock

import numpy as np

from entailment.dto import EntailmentRequest
from entailment.services import EntailmentService


class TestEntailmentService:
    def test_run_inference_returns_result(self):
        model_mock = Mock()
        model_mock.predict.return_value = np.array([[0.95, 0.03, 0.02]])

        provider = Mock()
        provider.get_model.return_value = model_mock

        service = EntailmentService(provider)

        result = service.run_inference(
            [
                EntailmentRequest(
                    premise="A",
                    hypothesis="B",
                )
            ]
        )

        assert len(result) == 1
