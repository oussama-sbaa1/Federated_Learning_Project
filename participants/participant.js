const fs = require('fs');
const path = require('path');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const { LocalModelTrainer } = require('./model');
const { FlowerBridgeTrainer } = require('./flower_bridge');
const { LinearRegressionTrainer } = require('./linear_trainer');

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
    // Auto-registration can be disabled (AUTO_REGISTER=false) so that the CLI registers the participant
    this.autoRegister = options.autoRegister !== undefined
      ? options.autoRegister
      : process.env.AUTO_REGISTER !== 'false';

    // Trainer selection:
    //   1) regression CSV file ("x,y" header)  -> LinearRegressionTrainer
    //   2) otherwise Flower bridge or the simple local vector trainer
    if (options.regressionFile) {
      this.trainer = new LinearRegressionTrainer(this.participantId, options.regressionFile);
    } else if (this.useFlower) {
      this.trainer = new FlowerBridgeTrainer(this.participantId, options.localData || [10, 10, 10]);
    } else {
      this.trainer = new LocalModelTrainer(this.participantId, options.localData);
    }

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

          // Local training step (regression, Flower AI or local vector trainer)
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
    if (this.autoRegister) {
      try {
        await this.register();
      } catch (err) {
        console.warn(`[${this.participantId}] Continuing execution in polling loop...`);
      }
    } else {
      console.log(`[${this.participantId}] Auto-registration disabled. Register this participant with the CLI.`);
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
// Usage: node participant.js <participant_id> <data_file_or_values> [coordinator_address]
//   data_file_or_values:
//     - regression CSV file whose first line is "x,y"      (e.g. data_A.csv)
//     - other file path (.json / .csv / .txt of numbers)
//     - comma-separated values (e.g. "10,12,15")
if (require.main === module) {
  const args = process.argv.slice(2);
  const participantId = args[0] || `participant_${Math.random().toString(36).substring(2, 6)}`;

  let localData = null;
  let regressionFile = null;

  if (args[1]) {
    const rawInput = args[1].trim();
    if (fs.existsSync(rawInput)) {
      try {
        const content = fs.readFileSync(rawInput, 'utf8').trim();
        if (/^x\s*,\s*y/i.test(content)) {
          // Regression dataset (x,y rows)
          regressionFile = rawInput;
          console.log(`Using regression dataset: ${rawInput}`);
        } else if (rawInput.endsWith('.json')) {
          const parsed = JSON.parse(content);
          localData = Array.isArray(parsed) ? parsed.map(Number) : parsed.data.map(Number);
        } else {
          // CSV / txt: comma, space or newline separated
          localData = content.split(/[\s,]+/).map(Number).filter(n => !isNaN(n));
        }
        if (localData) console.log(`Loaded ${localData.length} samples from file: ${rawInput}`);
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
    regressionFile,
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
