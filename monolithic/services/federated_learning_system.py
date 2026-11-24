
from monolithic.models.participant import Participant
from monolithic.models.training_config import TrainingConfig
from monolithic.models.training_job import TrainingJob
from monolithic.models.training_result import TrainingResult
from monolithic.models.job_status import JobStatus

from monolithic.services.local_trainer import LocalTrainer
from monolithic.services.aggregator import Aggregator


class FederatedLearningSystem:

    def __init__(self):
        self.participants: dict[str, Participant] = {}
        self.training_jobs: dict[str, TrainingJob] = {}

        self.trainer = LocalTrainer()
        self.aggregator = Aggregator()

    # F01 - Register a participant
    def register_participant(self, participant: Participant):

        if participant.participant_id in self.participants:
            raise ValueError("Participant already registered")

        self.participants[participant.participant_id] = participant

    # F02, F03 - Create a training job
    def create_training_job(
        self,
        config: TrainingConfig,
        participant_ids: list[str]
    ) -> TrainingJob:

        if not participant_ids:
            raise ValueError("At least one participant is required")

        if len(set(participant_ids)) != len(participant_ids):
            raise ValueError("Duplicate participant IDs")

        selected_participants = []

        for participant_id in participant_ids:
            if participant_id not in self.participants:
                raise ValueError(
                    f"Participant {participant_id} is not registered"
                )

            selected_participants.append(
                self.participants[participant_id]
            )

        job_id = f"JOB-{len(self.training_jobs) + 1:03d}"

        job = TrainingJob(
            job_id=job_id,
            participants=selected_participants,
            config=config
        )

        self.training_jobs[job_id] = job

        return job

    # F04 - Get training task
    def get_training_task(
        self,
        job_id: str,
        participant_id: str
    ) -> TrainingConfig:

        job = self._get_job(job_id)

        if job.status != JobStatus.RUNNING:
            raise ValueError("Training job is not running")

        participant_ids = [
            participant.participant_id
            for participant in job.participants
        ]

        if participant_id not in participant_ids:
            raise ValueError("Participant does not belong to this job")

        return job.config

    # F06 - Submit a local result
    def submit_result(
        self,
        job_id: str,
        result: TrainingResult
    ):

        job = self._get_job(job_id)

        if job.status != JobStatus.RUNNING:
            raise ValueError("Training job is not running")

        participant_ids = [
            participant.participant_id
            for participant in job.participants
        ]

        if result.participant_id not in participant_ids:
            raise ValueError("Unknown participant for this job")

        if any(
            r.participant_id == result.participant_id
            for r in job.local_results
        ):
            raise ValueError("Participant already submitted a result")

        job.local_results.append(result)

    # F04, F05, F07 - Start the training process
    def start_training(self, job_id: str):

        job = self._get_job(job_id)

        if job.status != JobStatus.PENDING:
            raise ValueError("Training job cannot be started")

        job.status = JobStatus.RUNNING

        try:
            for participant in job.participants:

                config = self.get_training_task(
                    job_id,
                    participant.participant_id
                )

                result = self.trainer.train(
                    participant,
                    config
                )

                self.submit_result(job_id, result)

            job.global_model = self.aggregator.aggregate(
                job.local_results
            )

            job.status = JobStatus.COMPLETED

        except Exception:
            job.status = JobStatus.FAILED
            raise

        return job

    # F08 - Get training status
    def get_training_status(self, job_id: str) -> TrainingJob:

        return self._get_job(job_id)

    # Internal helper
    def _get_job(self, job_id: str) -> TrainingJob:

        if job_id not in self.training_jobs:
            raise ValueError(f"Training job {job_id} not found")

        return self.training_jobs[job_id]
