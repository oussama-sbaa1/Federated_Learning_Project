
from dataclasses import dataclass


@dataclass
class TrainingConfig:
    learning_rate: float = 0.01
    rounds: int = 1
    model_parameters: float = 0.0

    def __post_init__(self):
        if self.learning_rate <= 0:
            raise ValueError("Learning rate must be positive")

        if self.rounds <= 0:
            raise ValueError("Rounds must be positive")
