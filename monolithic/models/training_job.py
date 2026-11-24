
from dataclasses import dataclass, field

from .participant import Participant
from .training_config import TrainingConfig
from .training_result import TrainingResult
from .job_status import JobStatus


@dataclass
class TrainingJob:
    job_id: str
    participants: list[Participant]
    config: TrainingConfig

    status: JobStatus = JobStatus.PENDING

    local_results: list[TrainingResult] = field(
        default_factory=list
    )

    global_model: float | None = None
