
from monolithic.models.participant import Participant
from monolithic.models.training_config import TrainingConfig
from monolithic.models.training_result import TrainingResult


class LocalTrainer:

    def train(
        self,
        participant: Participant,
        config: TrainingConfig
    ) -> TrainingResult:

        if not participant.local_data:
            raise ValueError(
                f"Participant {participant.participant_id} "
                "has no local data"
            )

        # Simulate local training by calculating the average
        local_weight = (
            sum(participant.local_data)
            / participant.sample_count
        )

        # Create the local training result
        result = TrainingResult(
            participant_id=participant.participant_id,
            local_weight=local_weight,
            sample_count=participant.sample_count
        )

        return result
