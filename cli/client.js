
const path = require("path");
const grpc = require("@grpc/grpc-js");
const protoLoader = require("@grpc/proto-loader");

const PROTO_PATH = process.env.PROTO_PATH || path.join(__dirname, "..", "proto", "federated.proto");
const COORDINATOR_ADDR = process.env.COORDINATOR_ADDR || "localhost:50051";

const definition = protoLoader.loadSync(PROTO_PATH, {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});
const proto = grpc.loadPackageDefinition(definition).federated;
const client = new proto.Coordinator(COORDINATOR_ADDR, grpc.credentials.createInsecure());

const call = (method, req) =>
  new Promise((resolve, reject) => {
    client[method](req, { deadline: Date.now() + 10000 }, (err, res) =>
      err ? reject(err) : resolve(res)
    );
  });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const show = (label, obj) => console.log(`[${label}]`, JSON.stringify(obj, null, 2));

async function register(participantId) {
  console.log(`-> gRPC RegisterParticipant -> ${COORDINATOR_ADDR}`);
  show("RegisterParticipant", await call("RegisterParticipant", { participant_id: participantId }));
}

async function createJob(numRounds, localEpochs, learningRate, ids) {
  console.log(`-> gRPC CreateJob -> ${COORDINATOR_ADDR}`);
  const res = await call("CreateJob", {
    config: {
      num_rounds: parseInt(numRounds, 10),
      local_epochs: parseInt(localEpochs, 10),
      learning_rate: parseFloat(learningRate),
    },
    participant_ids: ids.split(",").map((s) => s.trim()).filter(Boolean),
  });
  show("CreateJob", res);
  console.log(`\nJob created. Start it with: node client.js start ${res.job_id}`);
}

async function startTraining(jobId) {
  console.log(`-> gRPC StartTraining -> ${COORDINATOR_ADDR}`);
  show("StartTraining", await call("StartTraining", { job_id: jobId }));
}

async function getStatus(jobId) {
  const res = await call("GetTrainingStatus", { job_id: jobId });
  console.log(
    `[GetTrainingStatus] job=${res.job_id} status=${res.status} ` +
      `round=${res.current_round}/${res.num_rounds}`
  );
  return res;
}

async function status(jobId) {
  console.log(`-> gRPC GetTrainingStatus -> ${COORDINATOR_ADDR}`);
  const res = await getStatus(jobId);
  const w = res.global_weights && res.global_weights.weights;
  if (w && w.length) console.log("Global weights:", w);
}

async function watch(jobId) {
  for (;;) {
    const res = await getStatus(jobId);
    if (res.status === "COMPLETED" || res.status === "FAILED") {
      console.log(`\nFinal status: ${res.status}`);
      console.log("Final global weights:", (res.global_weights && res.global_weights.weights) || []);
      return;
    }
    await sleep(2000);
  }
}

function need(args, n, usage) {
  if (args.length < n) throw new Error(`usage: ${usage}`);
}

async function main() {
  const [cmd, ...a] = process.argv.slice(2);
  try {
    switch (cmd) {
      case "register":
        need(a, 1, "register <participant_id>");
        await register(a[0]);
        break;
      case "create":
        need(a, 4, "create <num_rounds> <local_epochs> <learning_rate> <id1,id2,...>");
        await createJob(a[0], a[1], a[2], a[3]);
        break;
      case "start":
        need(a, 1, "start <job_id>");
        await startTraining(a[0]);
        break;
      case "status":
        need(a, 1, "status <job_id>");
        await status(a[0]);
        break;
      case "watch":
        need(a, 1, "watch <job_id>");
        await watch(a[0]);
        break;
      default:
        console.log("Commands: register | create | start | status | watch");
    }
  } catch (err) {
    console.error("Error:", err.code ? `gRPC ${err.code}: ${err.details || err.message}` : err.message);
    process.exitCode = 1;
  } finally {
    client.close();
  }
}

main();