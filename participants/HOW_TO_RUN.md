# How to Run the Participant Service

This guide walks through running the Federated Learning participants alongside the Python coordinator and the Node.js management CLI using **`uv`**.

## Prerequisites

- **Node.js** 18 or higher
- **uv** (Python package and project manager) with Python 3.11+

From the repository root (`Federated_Learning_Project`), sync the Python environment and install the Node.js dependencies:

```powershell
uv sync
npm install --prefix participants
npm install --prefix cli
```

---

## Option 1: Automated Integration Test

To verify the full multi-language workflow in one command, run:

```powershell
node participants/test_integration.js
```

This script uses `uv run` to start the Python coordinator, launches one Node.js Flower participant (`flower_node_1`) and one Python Flower participant (`flower_py_2`), creates a 2-round job, and prints the FedAvg updates until the job finishes.

---

## Option 2: Step-by-Step Distributed Demo (4 Terminals)

Open four PowerShell terminals at the repository root (`Federated_Learning_Project`).

### Terminal 1 — Start the Coordinator (Python via `uv`)

```powershell
$env:PYTHONPATH="coordinator"
uv run python coordinator/server.py
```

Wait until you see:
```text
Coordinator listening on port 50051
```

### Terminal 2 — Start Participant 1 (Node.js + Flower AI)

You can pass a comma-separated vector directly, or point to a `.csv`, `.txt`, or `.json` file:

```powershell
# Inline vector
node participants/participant.js flower_node_1 10,10,10 localhost:50051

# Or load from a file
node participants/participant.js flower_node_1 participants/data_A.csv localhost:50051
```

### Terminal 3 — Start Participant 2 (Python + Flower AI via `uv`)

```powershell
$env:PYTHONPATH="coordinator;participants"

# Inline vector
uv run python participants/participant.py flower_py_2 30,30,30 localhost:50051

# Or load from a file
uv run python participants/participant.py flower_py_2 participants/data_B.json localhost:50051
```

### Terminal 4 — Create, Start, and Watch the Job (Management CLI)

Use the management CLI in `cli/client.js` to create a job targeting the two running participants (`flower_node_1` and `flower_py_2`):

```powershell
# 1. Create a job: 2 rounds, 1 local epoch, learning rate 0.5
node cli/client.js create 2 1 0.5 flower_node_1,flower_py_2

# 2. Start training (replace job1 if the CLI returned a different job_id)
node cli/client.js start job1

# 3. Watch progress until completion
node cli/client.js watch job1
```

> **Note:** Both participants register themselves with the coordinator on startup. If you register them first with `node cli/client.js register <id>`, they still connect and poll for tasks normally.

---

## Using Your Own Dataset

Both `participant.js` and `participant.py` read custom numeric vectors from:
1. **CLI argument**: e.g. `"10.5,12.0,14.5,11.0,13.5"`
2. **CSV / TXT file**: numbers separated by commas, spaces, or newlines (see `participants/data_A.csv`)
3. **JSON file**: an array of numbers like `[28.0, 31.5, 29.0, 30.5, 32.0]` or `{"data": [...]}` (see `participants/data_B.json`)

All participants in the same job must use vectors of the **same length** so the coordinator can aggregate weights with FedAvg.

---

## Expected Result

With `flower_node_1` holding `[10, 10, 10]`, `flower_py_2` holding `[30, 30, 30]`, `num_rounds = 2`, and `learning_rate = 0.5`:

- **Round 1**: P1 submits `[5, 5, 5]`, P2 submits `[15, 15, 15]` → Coordinator FedAvg = `[10.0, 10.0, 10.0]`
- **Round 2**: P1 submits `[10, 10, 10]`, P2 submits `[20, 20, 20]` → Coordinator FedAvg = `[15.0, 15.0, 15.0]`
- **Final status**: `COMPLETED` (both participants receive `FINISHED` and exit)
