def fedavg(results):
    """results: liste de (poids, num_samples). Retourne la moyenne pondérée."""
    total = sum(n for _, n in results)
    size = len(results[0][0])
    return [sum(n * w[i] for w, n in results) / total for i in range(size)]