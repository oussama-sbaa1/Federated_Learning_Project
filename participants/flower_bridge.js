const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Node.js bridge to Flower AI Client using uv.
 * Delegates the local fit() training step to the Flower Python NumPyClient.
 */
class FlowerBridgeTrainer {
  constructor(participantId, localData = [10, 10, 10]) {
    this.participantId = participantId;
    this.localData = localData;
    this.projectRoot = path.resolve(__dirname, '..');
  }

  getNumSamples() {
    return this.localData.length;
  }

  /**
   * Resolves the uv command or virtual environment Python executable.
   */
  getPythonCommand(script) {
    const winVenv = path.join(this.projectRoot, '.venv', 'Scripts', 'python.exe');
    const unixVenv = path.join(this.projectRoot, '.venv', 'bin', 'python');
    if (fs.existsSync(winVenv) || fs.existsSync(unixVenv)) {
      return {
        cmd: 'uv',
        args: ['run', '--no-sync', 'python', '-c', script]
      };
    }
    return {
      cmd: 'uv',
      args: ['run', 'python', '-c', script]
    };
  }

  /**
   * Delegates local training step to Flower NumPyClient in Python via uv
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

      const { cmd, args } = this.getPythonCommand(script);
      const py = spawn(cmd, args, {
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
