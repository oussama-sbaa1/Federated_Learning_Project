from concurrent import futures
import grpc
import federated_pb2
import federated_pb2_grpc


class TrainingJob:
    def __init__(self, job_id, config, participant_ids):
        self.job_id = job_id
        self.config = config                          # the TrainingConfig (num_rounds, ...)
        self.participant_ids = list(participant_ids)  # e.g. ["A", "B"]
        self.status = federated_pb2.PENDING           # not started yet
        self.current_round = 0
        self.global_weights = [0.0]                   # the starting model
        self.round_results = {}                       # results received this round
class Coordinator(federated_pb2_grpc.CoordinatorServicer):
    def __init__(self):
        self.participants = set()   # registered ids; a set has no duplicates (as in Tran's diagram)
        self.jobs = {}              # job id -> TrainingJob
        self.next_job_number = 1    # to make ids: job1, job2, ...
    def RegisterParticipant(self, request, context):
        pid = request.participant_id
        if pid in self.participants:
            return federated_pb2.RegisterParticipantReply(success=False, message=f"{pid} is already registered")
        self.participants.add(pid)
        print(f"{pid} registered")
        return federated_pb2.RegisterParticipantReply(success=True, message=f"{pid} registered")
    def CreateJob(self, request, context):
        job_id = f"job{self.next_job_number}"
        self.next_job_number += 1
        self.jobs[job_id] = TrainingJob(job_id, request.config, request.participant_ids)
        print(f"{job_id} created for {list(request.participant_ids)}")
        return federated_pb2.CreateJobReply(job_id=job_id)
    def StartTraining(self, request, context):
        job = self.jobs.get(request.job_id)
        if not job:
            return federated_pb2.StartTrainingReply(success=False, message=f"{request.job_id} not found")
        if job.status != federated_pb2.PENDING:
            return federated_pb2.StartTrainingReply(success=False, message=f"{request.job_id} already started")
        job.status = federated_pb2.IN_PROGRESS
        job.current_round = 1
        print(f"{request.job_id} started")
        return federated_pb2.StartTrainingReply(success=True, message=f"{request.job_id} started")
    def GetTrainingStatus(self, request, context):
        job = self.jobs.get(request.job_id)
        if not job:
            context.abort(grpc.StatusCode.NOT_FOUND, f"{request.job_id} not found")
        return federated_pb2.TrainingStatus(
            job_id=job.job_id,
            status=job.status,
            current_round=job.current_round,
            num_rounds=job.config.num_rounds,
            global_weights=federated_pb2.ModelParameters(weights=job.global_weights),
        )
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    federated_pb2_grpc.add_CoordinatorServicer_to_server(Coordinator(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Coordinator listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
