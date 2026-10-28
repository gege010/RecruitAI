"""Shared numeric contracts for all production MCDM methods."""

import numpy as np


def validate_inputs(matrix, weights):
    values = np.asarray(matrix, dtype=float)
    vector = np.asarray(weights, dtype=float)
    if values.ndim != 2 or not values.shape[0] or not values.shape[1]:
        raise ValueError("Decision matrix must contain candidates and criteria.")
    if vector.ndim != 1 or len(vector) != values.shape[1]:
        raise ValueError("Weight count must match criteria count.")
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Scores must be finite and nonnegative.")
    if not np.isfinite(vector).all() or (vector < 0).any() or vector.sum() <= 0:
        raise ValueError("Weights must be finite, nonnegative, with a positive total.")
    return values, vector / vector.sum()
