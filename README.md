# Minimal Federated Learning Framework with gRPC

A small federated learning platform built as a service-oriented application. Independent processes communicate **only through gRPC**, with the contract defined in Protocol Buffers. Flower is used as a conceptual reference.

The project has two implementations: a centralized (monolithic) one and a distributed one. Every distributed component runs as its own process.

## Architecture

```
                    +--------------------------+
   Management       |   Coordinator Service    |       Participant A
   Client (CLI)     |   Python, gRPC server    |       Node.js
   Node.js  ------> |   - job management       | <---- polls tasks,
   create/start/    |   - task distribution    |       trains locally,
   status/watch     |   - weighted aggregation |       submits results
                    +--------------------------+
                                ^                       Participant B
                                |                       Node.js
                                +------------------ same flow
```

- **Coordinator (Python):** registers participants, creates and runs jobs, hands out tasks, aggregates results with weighted FedAvg.
- **Participants (Node.js):** keep their data locally. They poll the coordinator for a task, train locally, and submit the updated weights. The coordinator never connects to them.
- **Management client (Node.js):** a command-line tool to register participants, create and start jobs, and watch the status and final result.

Two programming languages are used (Python and Node.js).

## Repository structure

```
cli/            Management client (Node.js)
coordinator/    Coordinator service (Python): server, job manager, FedAvg, tests
participants/   Participant service (Node.js) and local training code, datasets
proto/          federated.proto (the gRPC contract)
monolith/       Centralized implementation
docs/           Diagrams, workflow, AI prompt list, extra guides
```

## gRPC contract

Defined in `proto/federated.proto`, service `Coordinator`:

| RPC | Used by | Purpose |
|---|---|---|
| `RegisterParticipant` | CLI, participants | Register a participant |
| `CreateJob` | CLI | Create a job from a `TrainingConfig` and a participant list |
| `StartTraining` | CLI | Start a job |
| `GetTrainingStatus` | CLI | Job status, current round and global weights |
| `GetTrainingTask` | Participants | Fetch the task for the current round (`WAIT`, `TASK_READY`, `FINISHED`) |
| `SubmitTrainingResult` | Participants | Send updated weights, number of samples and loss |

A **job** is one federated training run: `num_rounds`, `local_epochs`, `learning_rate` and the list of participant ids. The training task itself is implemented locally by each participant.

## The learning task

Each participant fits a linear regression `y = w*x + b` on its own private data. The model is two numbers (`weights = [w, b]`).

- Data follows `y = 3x + 2 + noise`. Participant A holds 60 samples with x in [0, 0.5], participant B holds 140 samples with x in [0.5, 1].
- Each round, a participant starts from the global weights, runs `local_epochs` gradient descent epochs on its data, and returns the new weights, its sample count and its loss.
- The coordinator averages the weights, **weighted by the number of samples**:
  `w_global = sum(n_i * w_i) / sum(n_i)`
- With `5 rounds, 100 epochs, learning rate 0.5` the global model converges to about `w = 3.08, b = 1.93` (a centralized fit on all data gives `3.04, 1.98`), without any participant sharing its data.

Avoid learning rates of about 0.8 or higher: the training diverges.

The simple scenario from the assignment also works: participants with local results 10, 20 and 30 give a global average of 20.

## Requirements

- Python 3.9+ with `grpcio` and `grpcio-tools`
- Node.js 18+
- Optional, for the Flower-based participant path: `pip install flwr numpy`

## Installation

```bash
git clone https://github.com/oussama-sbaa1/Federated_Learning_Project.git
cd Federated_Learning_Project

pip install grpcio grpcio-tools
cd cli && npm install && cd ..
cd participants && npm install && cd ..
```

`node_modules` is not committed, so run `npm install` in each Node.js folder.

To regenerate the Python gRPC code after changing the proto:

```bash
python -m grpc_tools.protoc -I proto --python_out=coordinator --grpc_python_out=coordinator proto/federated.proto
```

## Running the demo (single machine)

Open four terminals from the project root.

**1. Coordinator**

```bash
cd coordinator
python server.py
```

**2. Participant A and 3. Participant B** (two separate terminals)

```bash
cd participants
node participant.js participant-A data_A.csv
node participant.js participant-B data_B.csv
```

Usage: `node participant.js <participant_id> <data_file_or_values> [coordinator_address]`

A participant registers itself when it starts. To register through the CLI instead (as in the demo scenario), start the participants with auto-registration disabled:

```powershell
$env:AUTO_REGISTER="false"        # PowerShell
# AUTO_REGISTER=false node ...    # Linux / macOS
node participant.js participant-A data_A.csv
```

**4. Management client**

```bash
cd cli
node client.js register participant-A      # only if AUTO_REGISTER=false
node client.js register participant-B
node client.js create 5 100 0.5 participant-A,participant-B
node client.js start job1
node client.js watch job1
```

Expected result: the status goes from `IN_PROGRESS` to `COMPLETED` and the final global weights are about `[3.08, 1.93]`. The coordinator terminal logs registrations and job events, and each participant terminal logs the tasks it received, its local training and the result it submitted.

## Management client reference

| Command | gRPC call | Description |
|---|---|---|
| `register <participant_id>` | `RegisterParticipant` | Register a participant |
| `create <rounds> <epochs> <lr> <id1,id2,...>` | `CreateJob` | Create a job, prints the `job_id` |
| `start <job_id>` | `StartTraining` | Start the job |
| `status <job_id>` | `GetTrainingStatus` | Print the status once |
| `watch <job_id>` | `GetTrainingStatus` | Poll until `COMPLETED` or `FAILED`, print final weights |

Environment variables for the CLI:

- `COORDINATOR_ADDR` coordinator address, default `localhost:50051`
- `PROTO_PATH` path to the proto file, default `../proto/federated.proto`

## Running on several machines

The coordinator listens on port `50051` on all interfaces. Participants and the CLI only need to reach it:

```bash
node participant.js participant-A data_A.csv 192.168.1.20:50051
```

Open TCP port 50051 in the firewall of the coordinator machine. See `docs/MULTI_PC_DEMO.md` for the full guide.

## Generating the datasets

The datasets `data_A.csv` and `data_B.csv` are included in `participants/`. To regenerate them:

```bash
cd participants
python generate_data.py .
```

## Tests

```bash
cd coordinator
python test_aggregation.py
python test_client.py
```
