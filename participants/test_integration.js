const { spawn } = require('child_process');
const path = require('path');

console.log('=== Starting Flower AI Cross-Language Integration Test (uv) ===');

const projectRoot = path.resolve(__dirname, '..');

// 1. Start Python Coordinator Server via uv
console.log('1. Starting Coordinator Service (uv run python)...');
const coordinator = spawn('uv', ['run', '--no-sync', 'python', 'coordinator/server.py'], {
  cwd: projectRoot,
  env: { ...process.env, PYTHONPATH: path.join(projectRoot, 'coordinator') }
});

coordinator.stdout.on('data', (d) => process.stdout.write(`[Coordinator] ${d}`));
coordinator.stderr.on('data', (d) => process.stderr.write(`[Coordinator ERR] ${d}`));

setTimeout(() => {
  // 2. Start Participant 1 (Node.js using Flower AI Bridge)
  console.log('2. Starting Participant 1 (Node.js with Flower Bridge)...');
  const participant1 = spawn('node', ['participants/participant.js', 'flower_node_1', '10,10,10'], {
    cwd: projectRoot
  });
  participant1.stdout.on('data', (d) => process.stdout.write(`[Node Flower P1] ${d}`));

  // 3. Start Participant 2 (Direct Python Flower NumPyClient via uv)
  console.log('3. Starting Participant 2 (uv run python Flower NumPyClient)...');
  const participant2 = spawn('uv', ['run', '--no-sync', 'python', 'participants/participant.py', 'flower_py_2', '30,30,30'], {
    cwd: projectRoot,
    env: { ...process.env, PYTHONPATH: `${path.join(projectRoot, 'coordinator')}${path.delimiter}${path.join(projectRoot, 'participants')}` }
  });
  participant2.stdout.on('data', (d) => process.stdout.write(`[Python Flower P2] ${d}`));

  // 4. Trigger training job from client
  setTimeout(() => {
    console.log('4. Creating and starting training job from client...');
    const client = spawn('uv', [
      'run',
      '--no-sync',
      'python',
      '-c',
      `
import time, grpc, sys
sys.path.insert(0, "coordinator")
import federated_pb2 as pb, federated_pb2_grpc as rpc

stub = rpc.CoordinatorStub(grpc.insecure_channel("localhost:50051"))
cfg = pb.TrainingConfig(num_rounds=2, local_epochs=1, learning_rate=0.5)
job = stub.CreateJob(pb.CreateJobRequest(config=cfg, participant_ids=["flower_node_1", "flower_py_2"]))
print("Job created:", job.job_id)
stub.StartTraining(pb.StartTrainingRequest(job_id=job.job_id))

for _ in range(15):
    s = stub.GetTrainingStatus(pb.GetTrainingStatusRequest(job_id=job.job_id))
    print("Job status:", pb.JobStatus.Name(s.status), "Round:", s.current_round, "Weights:", list(s.global_weights.weights))
    if s.status in (pb.COMPLETED, pb.FAILED):
        break
    time.sleep(1)
`
    ], {
      cwd: projectRoot,
      env: { ...process.env, PYTHONPATH: path.join(projectRoot, 'coordinator') }
    });

    client.stdout.on('data', (d) => process.stdout.write(`[Client] ${d}`));
    client.stderr.on('data', (d) => process.stderr.write(`[Client ERR] ${d}`));

    client.on('close', (code) => {
      console.log('=== Test finished with exit code:', code, '===');
      participant1.kill();
      participant2.kill();
      coordinator.kill();
      process.exit(code);
    });
  }, 3000);

}, 1500);
