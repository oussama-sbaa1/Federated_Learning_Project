/**
 * Local linear regression for a federated participant.
 * Model: y = w * x + b      -> weights = [w, b]
 * Loss : mean squared error (MSE)
 *
 * Fits the existing proto:
 *   global_weights.weights   -> input  [w, b]  (empty on round 1)
 *   updated_weights.weights  -> output [w, b]
 *   num_samples, loss        -> returned in TrainingResult
 */
const fs = require("fs");

// Load a CSV file with header "x,y"
function loadCsv(file) {
  const lines = fs.readFileSync(file, "utf8").trim().split(/\r?\n/).slice(1);
  const xs = [];
  const ys = [];
  for (const line of lines) {
    const [x, y] = line.split(",").map(Number);
    if (Number.isFinite(x) && Number.isFinite(y)) {
      xs.push(x);
      ys.push(y);
    }
  }
  return { xs, ys };
}

function mse(w, b, data) {
  let sum = 0;
  for (let i = 0; i < data.xs.length; i++) {
    const err = w * data.xs[i] + b - data.ys[i];
    sum += err * err;
  }
  return sum / data.xs.length;
}

/**
 * Train locally starting from the global weights.
 * @param {number[]} globalWeights  [w, b] or [] on the first round
 * @param {{xs:number[], ys:number[]}} data  private local data
 * @param {number} learningRate     from TrainingConfig.learning_rate
 * @param {number} epochs           from TrainingConfig.local_epochs
 * @returns {{weights:number[], numSamples:number, loss:number}}
 */
function trainLocal(globalWeights, data, learningRate, epochs) {
  let w = globalWeights && globalWeights.length === 2 ? globalWeights[0] : 0;
  let b = globalWeights && globalWeights.length === 2 ? globalWeights[1] : 0;
  const n = data.xs.length;

  for (let e = 0; e < epochs; e++) {
    let gradW = 0;
    let gradB = 0;
    for (let i = 0; i < n; i++) {
      const err = w * data.xs[i] + b - data.ys[i];
      gradW += 2 * err * data.xs[i];
      gradB += 2 * err;
    }
    w -= (learningRate * gradW) / n;
    b -= (learningRate * gradB) / n;
  }

  return { weights: [w, b], numSamples: n, loss: mse(w, b, data) };
}

module.exports = { loadCsv, trainLocal, mse };
