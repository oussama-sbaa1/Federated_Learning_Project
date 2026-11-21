import time, grpc
import federated_pb2 as pb, federated_pb2_grpc as rpc

stub = rpc.CoordinatorStub(grpc.insecure_channel("localhost:50051"))
job = stub.CreateJob(pb.CreateJobRequest(
    config=pb.TrainingConfig(num_rounds=3, local_epochs=1, learning_rate=0.5),
    participant_ids=["A", "B"]))
stub.StartTraining(pb.StartTrainingRequest(job_id=job.job_id))

while True:
    s = stub.GetTrainingStatus(pb.GetTrainingStatusRequest(job_id=job.job_id))
    print(pb.JobStatus.Name(s.status), "round", s.current_round, list(s.global_weights.weights))
    if s.status in (pb.COMPLETED, pb.FAILED):
        break
    time.sleep(1)