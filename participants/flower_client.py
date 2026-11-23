import sys
import numpy as np
import flwr as fl


class FlowerParticipantClient(fl.client.NumPyClient):
    """
    Standard Flower NumPyClient representing the Participant's local model.
    Encapsulates private local data and computes parameter updates using Flower API.
    """
    def __init__(self, participant_id: str, local_data: np.ndarray):
        self.participant_id = participant_id
        # Local private dataset: vector of numbers
        self.local_data = np.array(local_data, dtype=np.float64)
        # Initialize internal local model weights to match dimension of local data
        self.weights = np.zeros_like(self.local_data)

    def get_parameters(self, config=None):
        return [self.weights]

    def fit(self, parameters, config):
        """
        Train the model parameters on the private local data according to Flower client interface.
        """
        # Load incoming global weights
        if parameters and len(parameters) > 0 and len(parameters[0]) > 0:
            incoming = np.array(parameters[0], dtype=np.float64)
            if incoming.shape == self.local_data.shape:
                self.weights = incoming
            else:
                self.weights = np.zeros_like(self.local_data)

        lr = float(config.get("learning_rate", 0.5))
        epochs = int(config.get("local_epochs", 1))

        # Local SGD training steps on the private local vector
        for _ in range(epochs):
            gradient = -(self.local_data - self.weights)
            self.weights = self.weights - lr * gradient

        # Compute Mean Squared Error (MSE) loss
        loss = float(np.mean((self.local_data - self.weights) ** 2))
        num_samples = int(len(self.local_data))

        print(f"[{self.participant_id}] Flower fit() completed: loss={loss:.4f}, num_samples={num_samples}")
        return [self.weights], num_samples, {"loss": loss}

    def evaluate(self, parameters, config):
        if parameters and len(parameters) > 0:
            self.weights = np.array(parameters[0], dtype=np.float64)
        loss = float(np.mean((self.local_data - self.weights) ** 2))
        num_samples = int(len(self.local_data))
        return loss, num_samples, {"mse": loss}
