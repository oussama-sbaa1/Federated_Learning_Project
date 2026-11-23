const { spawn } = require('child_process');
const path = require('path');

/**
 * Node.js bridge to Flower AI Client.
 * When training is triggered, it can delegate the fit() step to the Flower Python Client.
 */
class FlowerBridgeTrainer {
  constructor(participantId, localData = [10, 10, 10]) {
    this.participantId = participantId;
    this.localData = localData;
    this.pythonPath = path.resolve(__dirname, '..', '.venv', 'Scripts', 'python.exe');
  }

  getNumSamples() {
    return this.localData.length;
  }

  /**
   * Delegates local training step to Flower NumPyClient in Python
   */
  async train(globalWeights, config) {
    return new Promise((resolve, reject) => {
      const script = `
import json, sys
import numpy as np
from flower_client import FlowerParticipantClient

local_data = json.loads('${JSON.stringify(this.localData)}')
global_weights = json.loads('${JSON.stringify(globalWeights || [])}')
cfg = json.loads('${JSON.stringify(config || {})}')

client = FlowerParticipantClient('${this.participantId}', np.array(local_data, dtype=np.float64))
params = [np.array(global_weights, dtype=np.float64)] if len(global_weights) > 0 else []
updated_params, num_samples, metrics = client.fit(params, cfg)

res = {
    "updatedWeights": updated_params[0].tolist(),
    "loss": metrics.get("loss", 0.0),
    "numSamples": num_samples
}
print(json.dumps(res))
`;

      const py = spawn(this.pythonPath, ['-c', script], {
        cwd: __dirname,
        env: { ...process.env, PYTHONPATH: __dirname }
      });

      let stdout = '';
      let stderr = '';

      py.stdout.on('data', (d) => { stdout += d.toString(); });
      py.stderr.on('data', (d) => { stderr += d.toString(); });

      py.on('close', (code) => {
        if (code !== 0) {
          return reject(new Error(`Flower Bridge process failed: ${stderr}`));
        }
        try {
          const lines = stdout.trim().split('\n');
          const lastLine = lines[lines.length - 1];
          const result = JSON.parse(lastLine);
          resolve(result);
        } catch (e) {
          reject(new Error(`Failed to parse Flower output: ${stdout}`));
        }
      });
    });
  }
}

module.exports = { FlowerBridgeTrainer };
