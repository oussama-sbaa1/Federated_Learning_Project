import grpc
import federated_pb2
import federated_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")
stub = federated_pb2_grpc.CoordinatorStub(channel)

reply = stub.RegisterParticipant(
     federated_pb2.RegisterParticipantRequest(participant_id="A")
)

print (reply.success)
print (reply.message)

