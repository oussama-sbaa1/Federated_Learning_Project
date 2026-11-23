const fs = require('fs');
const path = require('path');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const { LocalModelTrainer } = require('./model');
const { FlowerBridgeTrainer } = require('./flower_bridge');

// Load proto definitions
const PROTO_PATH = path.resolve(__dirname, '..', 'proto', 'federated.proto');
const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const federatedProto = grpc.loadPackageDefinition(packageDefinition).federated;

class ParticipantService {
  constructor(options = {}) {
    this.participantId = options.participantId || `participant_${Math.random().toString(36).substring(2, 7)}`;
    this.serverAddress = options.serverAddress || 'localhost:50051';
    this.pollIntervalMs = options.pollIntervalMs || 1000;
    this.useFlower = options.useFlower !== undefined ? options.useFlower : true;
    this.trainer = this.useFlower
      ? new FlowerBridgeTrainer(this.participantId, options.localData || [10, 10, 10])
      : new LocalModelTrainer(this.participantId, options.localData);
    this.client = new federatedProto.Coordinator(
      this.serverAddress,
      grpc.credentials.createInsecure()
    );
    this.isRunning = false;
    this.pollTimer = null;
    this.processedRounds = new Set();
    this.knownJobs = new Set();
  }

  register() {
    return new Promise((resolve, reject) => {
      this.client.RegisterParticipant({ participant_id: this.participantId }, (err, response) => {
        if (err) {
          console.error(`[${this.participantId}] Registration error:`, err.message);
          return reject(err);
        }
        console.log(`[${this.participantId}] Registration response: ${response.message} (success=${response.success})`);
        resolve(response);
      });
    });
  }

  getTrainingTask() {
    return new Promise((resolve, reject) => {
      this.client.GetTrainingTask({ participant_id: this.participantId }, (err, response) => {
        if (err) return reject(err);
        resolve(response);
      });
    });
  }

  submitTrainingResult(result) {
    return new Promise((resolve, reject) => {
      this.client.SubmitTrainingResult(result, (err, response) => {
        if (err) return reject(err);
        resolve(response);
      });
    });
  }

  async step() {
    try {
      const taskReply = await this.getTrainingTask();
      const state = taskReply.state;

      if (state === 'TASK_READY' || state === 1) {
        const task = taskReply.task;
        this.knownJobs.add(task.job_id);
        const roundKey = `${task.job_id}_r${task.round_number}`;

        if (!this.processedRounds.has(roundKey)) {
          console.log(`[${this.participantId}] Received task for Job ${task.job_id}, Round ${task.round_number}`);
          const incomingWeights = (task.global_weights && task.global_weights.weights) || [];
          console.log(`[${this.participantId}] Current global weights:`, incomingWeights);

          // Local training step via Flower AI or local trainer
          const { updatedWeights, loss, numSamples } = await this.trainer.train(
            incomingWeights,
            task.config
          );

          console.log(`[${this.participantId}] Training complete: Loss=${loss}, Samples=${numSamples}`);
          console.log(`[${this.participantId}] Local weights update:`, updatedWeights);

          // Submit update to Coordinator
          const submitReply = await this.submitTrainingResult({
            job_id: task.job_id,
            participant_id: this.participantId,
            round_number: task.round_number,
            updated_weights: { weights: updatedWeights },
            num_samples: numSamples,
            loss: loss
          });

          console.log(`[${this.participantId}] Submitted result: ${submitReply.message} (success=${submitReply.success})`);
          this.processedRounds.add(roundKey);
        }
      } else if (state === 'FINISHED' || state === 2) {
        if (this.knownJobs.size > 0) {
          console.log(`[${this.participantId}] Job finished. Stopping participant.`);
          this.stop();
          return;
        }
        // Coordinator has completed jobs from an earlier run; keep waiting for a new task
      } else {
        // State WAIT (0)
        // Heartbeat log at lower verbosity
      }
    } catch (err) {
      console.warn(`[${this.participantId}] Coordinator polling issue: ${err.message}. Retrying...`);
    }

    if (this.isRunning) {
      this.pollTimer = setTimeout(() => this.step(), this.pollIntervalMs);
    }
  }

  async start() {
    console.log(`[${this.participantId}] Starting participant service. Connecting to ${this.serverAddress}...`);
    try {
      await this.register();
    } catch (err) {
      console.warn(`[${this.participantId}] Continuing execution in polling loop...`);
    }

    this.isRunning = true;
    this.step();
  }

  stop() {
    this.isRunning = false;
    if (this.pollTimer) clearTimeout(this.pollTimer);
    console.log(`[${this.participantId}] Service stopped.`);
  }
}

// CLI execution handling
if (require.main === module) {
  const args = process.argv.slice(2);
  const participantId = args[0] || `participant_${Math.random().toString(36).substring(2, 6)}`;
  
  // Custom local data can be passed as:
  // 1) File path (e.g. data_A.csv or data_A.json)
  // 2) Comma-separated values (e.g. "10,12,15")
  let localData = null;
  if (args[1]) {
    const rawInput = args[1].trim();
    if (fs.existsSync(rawInput)) {
      try {
        const content = fs.readFileSync(rawInput, 'utf8').trim();
        if (rawInput.endsWith('.json')) {
          const parsed = JSON.parse(content);
          localData = Array.isArray(parsed) ? parsed.map(Number) : parsed.data.map(Number);
        } else {
          // CSV / txt: comma, space or newline separated
          localData = content.split(/[\s,]+/).map(Number).filter(n => !isNaN(n));
        }
        console.log(`Loaded ${localData.length} samples from file: ${rawInput}`);
      } catch (err) {
        console.warn(`Could not parse file ${rawInput}: ${err.message}. Falling back.`);
      }
    } else {
      localData = rawInput.split(/[\s,]+/).map(Number).filter(n => !isNaN(n));
    }
  }

  const serverAddress = args[2] || 'localhost:50051';

  console.log(`Initializing participant with ID: ${participantId}`);
  if (localData) {
    console.log(`Local dataset vector:`, localData);
  }

  const service = new ParticipantService({
    participantId,
    localData,
    serverAddress
  });

  service.start();

  process.on('SIGINT', () => {
    console.log(`\nShutting down participant ${participantId}...`);
    service.stop();
    process.exit(0);
  });
}

module.exports = { ParticipantService };
