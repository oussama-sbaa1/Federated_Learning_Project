import federated_pb2 as pb
from job_manager import TrainingJob
from fedavg import fedavg


def make_job():
    job = TrainingJob("j", pb.TrainingConfig(num_rounds=2), ["A", "B"])
    job.status, job.current_round = pb.IN_PROGRESS, 1
    job.reset_deadline()
    return job


def res(p, w, n, rnd=1):
    return pb.TrainingResult(job_id="j", participant_id=p, round_number=rnd,
                             updated_weights=pb.ModelParameters(weights=w), num_samples=n)


def test_fedavg_pure():
    assert fedavg([([10.0], 100), ([30.0], 300)]) == [25.0]


def test_weighted_aggregation():
    job = make_job()
    job.add_result(res("A", [10.0], 100))
    job.add_result(res("B", [30.0], 300))
    assert job.global_weights == [25.0]
    assert job.current_round == 2


def test_job_completes_after_last_round():
    job = make_job()
    for rnd in (1, 2):
        job.add_result(res("A", [10.0], 100, rnd))
        job.add_result(res("B", [30.0], 300, rnd))
    assert job.status == pb.COMPLETED


def test_wrong_round():
    ok, _ = make_job().add_result(res("A", [1.0], 10, rnd=2))
    assert not ok


def test_duplicate():
    job = make_job()
    job.add_result(res("A", [1.0], 10))
    ok, _ = job.add_result(res("A", [1.0], 10))
    assert not ok


def test_unknown_participant():
    ok, _ = make_job().add_result(res("Z", [1.0], 10))
    assert not ok


def test_zero_samples():
    ok, _ = make_job().add_result(res("A", [1.0], 0))
    assert not ok


def test_wrong_size():
    job = make_job()
    job.add_result(res("A", [1.0, 2.0], 10))
    ok, _ = job.add_result(res("B", [1.0], 10))
    assert not ok


def test_timeout_without_results_fails():
    job = make_job()
    job.deadline = 0
    job.check_timeout()
    assert job.status == pb.FAILED


def test_timeout_aggregates_partial_results():
    job = make_job()
    job.add_result(res("A", [10.0], 100))
    job.deadline = 0
    job.check_timeout()
    assert job.global_weights == [10.0]
    assert job.current_round == 2