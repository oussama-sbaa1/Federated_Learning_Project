/**
 * Local Model & Dataset simulation inspired by Flower / Federated Learning principles.
 * Keeps data local and computes parameter updates using local epochs and learning rate.
 */
class LocalModelTrainer {
  /**
   * @param {string} participantId
   * @param {number[]} localData - Private local data vector (simulated dataset)
   */
  constructor(participantId, localData = null) {
    this.participantId = participantId;
    // If not provided, generate a synthetic vector of local data values
    this.localData = localData && localData.length > 0 
      ? localData 
      : Array.from({ length: 5 }, () => parseFloat((Math.random() * 20 + 5).toFixed(2)));
  }

  /**
   * Returns the number of training samples locally available
   */
  getNumSamples() {
    return this.localData.length;
  }

  /**
   * Execute local training on the incoming global weights using training configuration
   * @param {number[]} globalWeights - Current global model weights
   * @param {object} config - Training configuration (learning_rate, local_epochs, etc.)
   * @returns {{ updatedWeights: number[], loss: number, numSamples: number }}
   */
  train(globalWeights, config) {
    const lr = config && config.learning_rate > 0 ? config.learning_rate : 0.5;
    const epochs = config && config.local_epochs > 0 ? config.local_epochs : 1;

    // Target represents the local dataset profile (e.g. mean value of local vector)
    const target = this.localData.reduce((acc, v) => acc + v, 0) / this.localData.length;

    // Initialize model weights if global weights were empty
    let weights = (globalWeights && globalWeights.length > 0)
      ? [...globalWeights]
      : Array(this.localData.length).fill(0.0);

    let currentLoss = 0;

    // Simulate local SGD training iterations
    for (let e = 0; e < epochs; e++) {
      weights = weights.map((w, idx) => {
        // Individual feature target from local data if dimensions match, else mean target
        const sampleTarget = this.localData[idx % this.localData.length];
        const gradient = -(sampleTarget - w);
        return parseFloat((w - lr * gradient).toFixed(4));
      });

      // Compute simple mean squared error loss
      currentLoss = weights.reduce((acc, w, idx) => {
        const sampleTarget = this.localData[idx % this.localData.length];
        return acc + Math.pow(sampleTarget - w, 2);
      }, 0) / weights.length;
    }

    return {
      updatedWeights: weights,
      loss: parseFloat(currentLoss.toFixed(4)),
      numSamples: this.getNumSamples()
    };
  }
}

module.exports = { LocalModelTrainer };
