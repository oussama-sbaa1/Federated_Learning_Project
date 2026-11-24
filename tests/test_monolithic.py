
import pytest

from monolithic.models.participant import Participant
from monolithic.models.training_config import TrainingConfig
from monolithic.models.training_result import TrainingResult
from monolithic.models.job_status import JobStatus

from monolithic.services.federated_learning_system import (
    FederatedLearningSystem
)
from monolithic.services.aggregator import Aggregator


@pytest.fixture
def system():
    """Create a system with three registered participants."""

    fed_system = FederatedLearningSystem()

    participants = [
        Participant("A", "Hospital A", [5, 10, 15]),
        Participant("B", "Hospital B", [10, 20, 30]),
        Participant("C", "Hospital C", [15, 30, 45])
    ]

    for participant in participants:
        fed_system.register_participant(participant)

    return fed_system


@pytest.fixture
def training_job(system):
    """Create a training job for the three participants."""

    return system.create_training_job(
        config=TrainingConfig(),
        participant_ids=["A", "B", "C"]
    )


# TEST 1: Participant registration
def test_register_participant(system):

    assert "A" in system.participants
    assert len(system.participants) == 3


# TEST 2: Duplicate participant registration
def test_register_duplicate_participant(system):

    duplicate = Participant("A", "Hospital A", [1, 2, 3])

    with pytest.raises(ValueError):
        system.register_participant(duplicate)


# TEST 3: Create a training job
def test_create_training_job(training_job):

    assert training_job.job_id == "JOB-001"
    assert training_job.status == JobStatus.PENDING
    assert len(training_job.participants) == 3


# TEST 4: Unknown participant
def test_create_job_with_unknown_participant(system):

    with pytest.raises(ValueError):
        system.create_training_job(
            TrainingConfig(),
            ["A", "UNKNOWN"]
        )


# TEST 5: Successful training
def test_start_training(system, training_job):

    system.start_training(training_job.job_id)

    assert training_job.status == JobStatus.COMPLETED
    assert len(training_job.local_results) == 3
    assert training_job.global_model == 20.0


# TEST 6: Duplicate result submission
def test_submit_duplicate_result(system, training_job):

    training_job.status = JobStatus.RUNNING

    result = TrainingResult(
        participant_id="A",
        local_weight=10.0,
        sample_count=3
    )

    system.submit_result(training_job.job_id, result)

    with pytest.raises(ValueError):
        system.submit_result(training_job.job_id, result)


# TEST 7: Aggregator with no results
def test_aggregate_empty_results():

    aggregator = Aggregator()

    with pytest.raises(ValueError):
        aggregator.aggregate([])


# TEST 8: Failed training
def test_failed_training(system, training_job):

    def simulate_failure(participant, config):
        raise RuntimeError("Simulated training error")

    system.trainer.train = simulate_failure

    with pytest.raises(RuntimeError):
        system.start_training(training_job.job_id)

    assert training_job.status == JobStatus.FAILED


# TEST 9: Unknown training job
def test_get_unknown_training_job(system):

    with pytest.raises(ValueError):
        system.get_training_status("JOB-999")


# TEST 10: Weighted aggregation
def test_weighted_aggregation():

    aggregator = Aggregator()

    results = [
        TrainingResult("A", 10.0, 3),
        TrainingResult("B", 20.0, 6)
    ]

    global_model = aggregator.aggregate(results)

    assert global_model == pytest.approx(16.6666667)
