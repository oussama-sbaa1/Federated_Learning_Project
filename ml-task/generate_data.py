"""
Generate local datasets for the federated linear regression task.

True relation: y = 3*x + 2 + noise
Each participant holds a different slice of the input range and a different
number of samples, so weighted averaging (by num_samples) actually matters.

Usage:  python generate_data.py [output_dir]      (default: participants)
"""
import csv
import os
import random
import sys

TRUE_W, TRUE_B, NOISE = 3.0, 2.0, 0.1


def make_dataset(n, x_min, x_max, rng):
    rows = []
    for _ in range(n):
        x = rng.uniform(x_min, x_max)
        y = TRUE_W * x + TRUE_B + rng.gauss(0, NOISE)
        rows.append((round(x, 5), round(y, 5)))
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y"])
        writer.writerows(rows)


def least_squares(rows):
    """Centralized closed-form fit, used only as a reference for the report."""
    n = len(rows)
    mx = sum(x for x, _ in rows) / n
    my = sum(y for _, y in rows) / n
    w = sum((x - mx) * (y - my) for x, y in rows) / sum((x - mx) ** 2 for x, _ in rows)
    return w, my - w * mx


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "participants"
    os.makedirs(out_dir, exist_ok=True)
    rng = random.Random(42)

    data_a = make_dataset(60, 0.0, 0.5, rng)    # participant A: 60 samples, x in [0, 0.5]
    data_b = make_dataset(140, 0.5, 1.0, rng)   # participant B: 140 samples, x in [0.5, 1]

    write_csv(os.path.join(out_dir, "data_A.csv"), data_a)
    write_csv(os.path.join(out_dir, "data_B.csv"), data_b)

    w, b = least_squares(data_a + data_b)
    print(f"Wrote data_A.csv ({len(data_a)} rows) and data_B.csv ({len(data_b)} rows) in {out_dir}/")
    print(f"True parameters       : w={TRUE_W}, b={TRUE_B}")
    print(f"Centralized reference : w={w:.3f}, b={b:.3f}")
