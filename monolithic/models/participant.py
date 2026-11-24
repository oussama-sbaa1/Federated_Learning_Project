
from dataclasses import dataclass


@dataclass
class Participant:
    participant_id: str
    name: str
    local_data: list[float]

    @property
    def sample_count(self) -> int:
        return len(self.local_data)
