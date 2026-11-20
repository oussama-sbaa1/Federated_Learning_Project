from concurrent import futures
import grpc
import federated_pb2
import federated_pb2_grpc

class Coordinator(federated_pb2_grpc.CoordinatorServicer):
    def __init__(self):
        self.participants = set()   # registered ids; a set has no duplicates (as in Tran's diagram)

    def RegisterParticipant(self, request, context):
        pid = request.participant_id
        if pid in self.participants:
            return federated_pb2.RegisterParticipantReply(success=False, message=f"{pid} is already registered")
        self.participants.add(pid)
        print(f"{pid} registered")
        return federated_pb2.RegisterParticipantReply(success=True, message=f"{pid} registered")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    federated_pb2_grpc.add_CoordinatorServicer_to_server(Coordinator(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Coordinator listening on port 50051")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()