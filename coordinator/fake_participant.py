import sys, time, grpc
import federated_pb2 as pb, federated_pb2_grpc as rpc

pid, value, n = sys.argv[1], float(sys.argv[2]), int(sys.argv[3])
stub = rpc.CoordinatorStub(grpc.insecure_channel("localhost:50051"))
stub.RegisterParticipant(pb.RegisterParticipantRequest(participant_id=pid))

while True:
    t = stub.GetTrainingTask(pb.GetTrainingTaskRequest(participant_id=pid))
    if t.state == pb.FINISHED:
        break
    if t.state == pb.TASK_READY:
        w = list(t.task.global_weights.weights) or [0.0]
        lr = t.task.config.learning_rate or 0.5
        new = [x + lr * (value - x) for x in w]      # "entraînement" local simulé
        r = stub.SubmitTrainingResult(pb.TrainingResult(
            job_id=t.task.job_id, participant_id=pid, round_number=t.task.round_number,
            updated_weights=pb.ModelParameters(weights=new), num_samples=n))
        print(pid, "round", t.task.round_number, "->", new, r.message)
    time.sleep(1)