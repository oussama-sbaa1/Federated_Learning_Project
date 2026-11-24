
from monolithic.models.training_result import TrainingResult


class Aggregator:

    def aggregate(
        self,
        results: list[TrainingResult]
    ) -> float:

        if not results:
            raise ValueError("No training results to aggregate")

        total_samples = sum(
            result.sample_count for result in results
        )

        if total_samples <= 0:
            raise ValueError("Total sample count must be positive")

        weighted_sum = sum(
            result.local_weight * result.sample_count
            for result in results
        )

        global_model = weighted_sum / total_samples

        return global_model
