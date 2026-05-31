from sentence_transformers import CrossEncoder
from django.conf import settings
from threading import Lock


class ModelProvider:
    _model = None
    _lock = Lock()

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # lock to prevent multiple load at 1st request
            with cls._lock:
                if cls._model is None:
                    cls._model = CrossEncoder(settings.ENTAILMENT_MODEL_NAME)

        return cls._model
