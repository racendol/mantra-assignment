from dataclasses import dataclass

from entailment.enum import EntailmentLabel


@dataclass
class EntailmentRequest:
    premise: str
    hypothesis: str


@dataclass
class EntailmentResult:
    label: EntailmentLabel
    score: float
