import threading, time
import federated_pb2
from fedavg import fedavg

ROUND_TIMEOUT = 30   # secondes d'attente par round


class TrainingJob:
    def __init__(self, job_id, config, participant_ids):
        self.job_id = job_id
        self.config = config
        self.participant_ids = list(participant_ids)
        self.status = federated_pb2.PENDING
        self.current_round = 0
        self.global_weights = []
        self.round_results = {}
        self.lock = threading.Lock()
        self.deadline = 0

    def reset_deadline(self):
        self.deadline = time.time() + ROUND_TIMEOUT

    def check_timeout(self):
        with self.lock:
            if self.status == federated_pb2.IN_PROGRESS and time.time() > self.deadline:
                if self.round_results:
                    self._aggregate()
                else:
                    self.status = federated_pb2.FAILED
                    print(f"[{self.job_id}] FAILED (timeout)")

    def add_result(self, r):
        with self.lock:
            if self.status != federated_pb2.IN_PROGRESS:
                return False, "job not in progress"
            if r.participant_id not in self.participant_ids:
                return False, f"{r.participant_id} not in this job"
            if r.round_number != self.current_round:
                return False, f"wrong round (expected {self.current_round})"
            if r.participant_id in self.round_results:
                return False, "already submitted this round"
            w = r.updated_weights.weights
            if r.num_samples <= 0 or len(w) == 0:
                return False, "invalid data (num_samples <= 0 or empty weights)"
            expected = len(self.global_weights) or next(
                (len(x.updated_weights.weights) for x in self.round_results.values()), len(w))
            if len(w) != expected:
                return False, f"expected {expected} weights, got {len(w)}"
            self.round_results[r.participant_id] = r
            if len(self.round_results) == len(self.participant_ids):
                self._aggregate()
            return True, "result accepted"

    def _aggregate(self):
        results = list(self.round_results.values())
        self.global_weights = fedavg(
            [(list(r.updated_weights.weights), r.num_samples) for r in results])
        print(f"[{self.job_id}] round {self.current_round} ({len(results)} results) -> {self.global_weights}")
        self.round_results = {}
        if self.current_round >= self.config.num_rounds:
            self.status = federated_pb2.COMPLETED
            print(f"[{self.job_id}] COMPLETED")
        else:
            self.current_round += 1
            self.reset_deadline()