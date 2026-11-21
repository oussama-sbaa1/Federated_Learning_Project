from concurrent import futures
import grpc
import federated_pb2
import federated_pb2_grpc
from job_manager import TrainingJob


class Coordinator(federated_pb2_grpc.CoordinatorServicer):
    def __init__(self):
        self.participants = set()
        self.jobs = {}
        self.next_job_number = 1

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
        job.reset_deadline()
        print(f"{request.job_id} started")
        return federated_pb2.StartTrainingReply(success=True, message=f"{request.job_id} started")

    def GetTrainingStatus(self, request, context):
        job = self.jobs.get(request.job_id)
        if not job:
            context.abort(grpc.StatusCode.NOT_FOUND, f"{request.job_id} not found")
        job.check_timeout()
        return federated_pb2.TrainingStatus(
            job_id=job.job_id,
            status=job.status,
            current_round=job.current_round,
            num_rounds=job.config.num_rounds,
            global_weights=federated_pb2.ModelParameters(weights=job.global_weights),
        )

    def GetTrainingTask(self, request, context):
        pid = request.participant_id
        finished = False
        for job in self.jobs.values():
            if pid not in job.participant_ids:
                continue
            job.check_timeout()
            if job.status == federated_pb2.IN_PROGRESS:
                if pid in job.round_results:
                    return federated_pb2.GetTrainingTaskReply(state=federated_pb2.WAIT)
                task = federated_pb2.TrainingTask(
                    job_id=job.job_id,
                    round_number=job.current_round,
                    config=job.config,
                    global_weights=federated_pb2.ModelParameters(weights=job.global_weights),
                )
                return federated_pb2.GetTrainingTaskReply(state=federated_pb2.TASK_READY, task=task)
            if job.status == federated_pb2.COMPLETED:
                finished = True
        state = federated_pb2.FINISHED if finished else federated_pb2.WAIT
        return federated_pb2.GetTrainingTaskReply(state=state)

    def SubmitTrainingResult(self, request, context):
        job = self.jobs.get(request.job_id)
        if not job:
            return federated_pb2.SubmitTrainingResultReply(success=False, message=f"{request.job_id} not found")
        ok, msg = job.add_result(request)
        return federated_pb2.SubmitTrainingResultReply(success=ok, message=msg)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    federated_pb2_grpc.add_CoordinatorServicer_to_server(Coordinator(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Coordinator listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()