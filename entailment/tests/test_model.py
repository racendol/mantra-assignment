from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from entailment.model import ModelProvider

import pytest


# reset cached model every test
@pytest.fixture(autouse=True)
def reset_model_provider():
    ModelProvider._model = None
    yield
    ModelProvider._model = None


class TestModelProvider:
    @patch("entailment.model.CrossEncoder")
    def test_loads_model_on_first_call(
        self,
        mock_cross_encoder,
    ):
        model = Mock()

        mock_cross_encoder.return_value = model

        result = ModelProvider.get_model()

        assert result is model

        mock_cross_encoder.assert_called_once()

    @patch("entailment.model.CrossEncoder")
    def test_returns_cached_model(
        self,
        mock_cross_encoder,
    ):
        model = Mock()

        mock_cross_encoder.return_value = model

        first = ModelProvider.get_model()
        second = ModelProvider.get_model()

        assert first is second

        mock_cross_encoder.assert_called_once()

    @patch("entailment.model.CrossEncoder")
    def test_uses_settings_model_name(
        self,
        mock_cross_encoder,
        settings,
    ):
        settings.ENTAILMENT_MODEL_NAME = "custom-model"

        mock_cross_encoder.return_value = Mock()

        ModelProvider.get_model()

        mock_cross_encoder.assert_called_once_with("custom-model")

    @patch("entailment.model.CrossEncoder")
    def test_concurrent_calls_load_once(
        self,
        mock_cross_encoder,
    ):
        model = Mock()

        mock_cross_encoder.return_value = model

        def load():
            return ModelProvider.get_model()

        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(
                executor.map(
                    lambda _: load(),
                    range(20),
                )
            )

        assert all(result is model for result in results)

        mock_cross_encoder.assert_called_once()
