
from monolithic.models.participant import Participant
from monolithic.models.training_config import TrainingConfig

from monolithic.services.federated_learning_system import (
    FederatedLearningSystem
)


# 1. Initialize the system
system = FederatedLearningSystem()


# 2. Create participants
participant_a = Participant(
    participant_id="A",
    name="Hospital A",
    local_data=[5, 10, 15]
)

participant_b = Participant(
    participant_id="B",
    name="Hospital B",
    local_data=[10, 20, 30]
)

participant_c = Participant(
    participant_id="C",
    name="Hospital C",
    local_data=[15, 30, 45]
)


# 3. Register participants
system.register_participant(participant_a)
system.register_participant(participant_b)
system.register_participant(participant_c)

print("===== PARTICIPANTS REGISTERED =====")
print("Participants:", list(system.participants.keys()))


# 4. Create training configuration
config = TrainingConfig(
    learning_rate=0.01,
    rounds=1,
    model_parameters=0.0
)


# 5. Create training job
job = system.create_training_job(
    config=config,
    participant_ids=["A", "B", "C"]
)

print("\n===== TRAINING JOB CREATED =====")
print("Job ID:", job.job_id)
print("Initial status:", job.status.value)


# 6. Start training
print("\n===== STARTING TRAINING =====")

system.start_training(job.job_id)


# 7. Display local results
print("\n===== LOCAL TRAINING RESULTS =====")

for result in job.local_results:
    print(
        f"Participant {result.participant_id}: "
        f"{result.local_weight}"
    )


# 8. Display final status
final_job = system.get_training_status(job.job_id)

print("\n===== FINAL TRAINING STATUS =====")
print("Job ID:", final_job.job_id)
print("Status:", final_job.status.value)
print("Global Model:", final_job.global_model)
