import sys
import os
import time
import grpc
import numpy as np

# Ensure coordinator proto imports are available
coordinator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "coordinator"))
if coordinator_path not in sys.path:
    sys.path.insert(0, coordinator_path)

import federated_pb2 as pb
import federated_pb2_grpc as rpc
from flower_client import FlowerParticipantClient


class FlowerParticipantService:
    """
    Participant Service powered by Flower AI:
    - Runs a Flower NumPyClient (FlowerParticipantClient) for local model training
    - Connects to the gRPC Coordinator Service via protobuf interfaces
    - Polls tasks, feeds global weights into Flower client.fit(), and submits results
    """
    def __init__(self, participant_id: str, local_vector: list, server_address: str = "localhost:50051"):
        self.participant_id = participant_id
        self.server_address = server_address
        self.channel = grpc.insecure_channel(server_address)
        self.stub = rpc.CoordinatorStub(self.channel)
        
        # Initialize the Flower AI Client
        self.flower_client = FlowerParticipantClient(
            participant_id=participant_id,
            local_data=np.array(local_vector, dtype=np.float64)
        )
        self.processed_rounds = set()
        self.known_jobs = set()

    def register(self):
        req = pb.RegisterParticipantRequest(participant_id=self.participant_id)
        reply = self.stub.RegisterParticipant(req)
        print(f"[{self.participant_id}] Flower Client Registered: {reply.message} (success={reply.success})")

    def run(self):
        print(f"[{self.participant_id}] Starting Flower Participant loop. Local vector: {self.flower_client.local_data.tolist()}...")
        self.register()

        while True:
            try:
                task_reply = self.stub.GetTrainingTask(pb.GetTrainingTaskRequest(participant_id=self.participant_id))
                state = task_reply.state

                if state == pb.FINISHED:
                    if self.known_jobs:
                        print(f"[{self.participant_id}] All assigned Flower training rounds finished. Stopping.")
                        break
                    else:
                        time.sleep(1)
                        continue

                if state == pb.TASK_READY:
                    task = task_reply.task
                    self.known_jobs.add(task.job_id)
                    round_key = f"{task.job_id}_{task.round_number}"

                    if round_key not in self.processed_rounds:
                        print(f"[{self.participant_id}] Flower AI received task for Job {task.job_id}, Round {task.round_number}")
                        incoming_weights = list(task.global_weights.weights)
                        print(f"[{self.participant_id}] Current global weights: {incoming_weights}")

                        # Package config for Flower NumPyClient
                        config = {
                            "learning_rate": task.config.learning_rate or 0.5,
                            "local_epochs": task.config.local_epochs or 1,
                        }

                        # Invoke standard Flower NumPyClient fit()
                        parameters = [incoming_weights] if incoming_weights else []
                        updated_params, num_samples, metrics = self.flower_client.fit(parameters, config)

                        updated_weights = updated_params[0].tolist()
                        loss = float(metrics.get("loss", 0.0))
                        print(f"[{self.participant_id}] Local weights update: {updated_weights}")

                        # Submit updated weights to Coordinator via gRPC
                        result_msg = pb.TrainingResult(
                            job_id=task.job_id,
                            participant_id=self.participant_id,
                            round_number=task.round_number,
                            updated_weights=pb.ModelParameters(weights=updated_weights),
                            num_samples=num_samples,
                            loss=loss
                        )
                        reply = self.stub.SubmitTrainingResult(result_msg)
                        print(f"[{self.participant_id}] Submitted Flower result: {reply.message}")
                        self.processed_rounds.add(round_key)

                time.sleep(1)
            except grpc.RpcError as e:
                print(f"[{self.participant_id}] gRPC error: {e.details()}. Retrying...")
                time.sleep(1)


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "participant_flower"
    
    # Custom local data can be passed as:
    # 1) File path (e.g. data_B.csv, data_B.txt, data_B.json)
    # 2) Comma-separated or space-separated numbers (e.g. "30,32,35")
    if len(sys.argv) > 2:
        val_arg = sys.argv[2].strip()
        if os.path.exists(val_arg):
            try:
                with open(val_arg, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if val_arg.endswith(".json"):
                    import json
                    parsed = json.loads(content)
                    vec = [float(x) for x in (parsed if isinstance(parsed, list) else parsed.get("data", []))]
                else:
                    import re
                    vec = [float(x) for x in re.split(r"[\s,]+", content) if x.strip()]
                print(f"Loaded {len(vec)} samples from file: {val_arg}")
            except Exception as e:
                print(f"Error reading file {val_arg}: {e}. Falling back.")
                vec = [20.0, 20.0, 20.0]
        elif "," in val_arg:
            vec = [float(x) for x in val_arg.split(",") if x.strip()]
        else:
            try:
                v = float(val_arg)
                vec = [v, v, v]
            except ValueError:
                vec = [20.0, 20.0, 20.0]
    else:
        vec = [15.0, 15.0, 15.0]

    srv = sys.argv[3] if len(sys.argv) > 3 else "localhost:50051"

    service = FlowerParticipantService(pid, vec, srv)
    service.run()
