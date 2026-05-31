import numpy as np

from entailment.dto import EntailmentRequest, EntailmentResult
from entailment.enum import EntailmentLabel
from entailment.model import ModelProvider

LABEL_MAPPING = (EntailmentLabel.ENTAILMENT, EntailmentLabel.NO_ENTAILMENT)


class EntailmentService:
    def __init__(self, provider: ModelProvider):
        self.provider = provider

    def run_inference(
        self,
        requests: list[EntailmentRequest],
    ) -> list[EntailmentResult]:
        input_list = [(request.hypothesis, request.premise) for request in requests]

        scores = self.provider.get_model().predict(input_list, apply_softmax=True)

        # combine neutral and contradiction to no entailment
        binary_scores = np.stack(
            [
                scores[:, 0],  # entail
                scores[:, 1] + scores[:, 2],  # neutral + contradiction
            ],
            axis=1,
        )

        predicted_indices = binary_scores.argmax(axis=1)
        predicted_scores = binary_scores.max(axis=1)

        return [
            EntailmentResult(
                label=LABEL_MAPPING[predicted_indices[i]],
                score=predicted_scores[i],
            )
            for i in range(len(predicted_indices))
        ]


entailment_service = EntailmentService(ModelProvider())
