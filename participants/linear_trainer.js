/**
 * Drop-in trainer for participant.js.
 * Same interface as LocalModelTrainer / FlowerBridgeTrainer:
 *     await trainer.train(incomingWeights, taskConfig)
 *       -> { updatedWeights, loss, numSamples }
 */
const { loadCsv, trainLocal } = require('./linear_model');

class LinearRegressionTrainer {
  constructor(participantId, csvPath) {
    this.participantId = participantId;
    this.data = loadCsv(csvPath);
    if (this.data.xs.length === 0) {
      throw new Error(`No valid "x,y" rows found in ${csvPath}`);
    }
    console.log(`[${participantId}] Loaded ${this.data.xs.length} regression samples from ${csvPath}`);
  }

  async train(incomingWeights, config) {
    const lr = Number(config.learning_rate) || 0.1;
    const epochs = Number(config.local_epochs) || 1;
    const r = trainLocal(incomingWeights, this.data, lr, epochs);
    return { updatedWeights: r.weights, loss: r.loss, numSamples: r.numSamples };
  }
}

module.exports = { LinearRegressionTrainer };
