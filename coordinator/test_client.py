import grpc
import federated_pb2
import federated_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")
stub = federated_pb2_grpc.CoordinatorStub(channel)
# 1. register both participants
for pid in ["A", "B"]:
    reply = stub.RegisterParticipant(federated_pb2.RegisterParticipantRequest(participant_id=pid))
    print(reply.success, reply.message)

# 2. create a job: 3 rounds, with A and B
config = federated_pb2.TrainingConfig(num_rounds=3, local_epochs=1, learning_rate=0.1)
job = stub.CreateJob(federated_pb2.CreateJobRequest(config=config, participant_ids=["A", "B"]))
print("created", job.job_id)

# 3. start it
reply = stub.StartTraining(federated_pb2.StartTrainingRequest(job_id=job.job_id))
print(reply.success, reply.message)

# 4. ask for its status
status = stub.GetTrainingStatus(federated_pb2.GetTrainingStatusRequest(job_id=job.job_id))
print(status)