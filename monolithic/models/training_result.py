
from dataclasses import dataclass


@dataclass
class TrainingResult:
    participant_id: str
    local_weight: float
    sample_count: int

    def __post_init__(self):
        if self.sample_count <= 0:
            raise ValueError("Sample count must be positive")
