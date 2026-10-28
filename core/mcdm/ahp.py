"""
AHP (Analytic Hierarchy Process) weight derivation module.

Steps:
  1. User provides an n×n pairwise comparison matrix (Saaty 1–9 scale).
  2. Normalize each column → compute priority vector (weights).
  3. Compute λ_max → CI → CR.
  4. Weights are valid if CR < 0.10.
"""

from __future__ import annotations

import numpy as np
import logging

logger = logging.getLogger(__name__)


# Saaty Random Consistency Index table
_RI = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


def compute_ahp(matrix: list[list[float]]) -> dict:
    """
    Run AHP on a pairwise comparison matrix.

    Args:
        matrix: n×n list of floats (Saaty scale 1/9 … 9).

    Returns:
        dict with keys:
            weights (list[float])   – priority vector summing to 1
            lambda_max (float)
            consistency_index (float)
            consistency_ratio (float)
            is_valid (bool)         – CR < 0.10
    """
    A = np.array(matrix, dtype=float)
    if A.ndim != 2 or A.shape[0] == 0 or A.shape[0] != A.shape[1]:
        raise ValueError("Pairwise matrix must be nonempty and square.")
    if not np.isfinite(A).all() or (A <= 0).any():
        raise ValueError("Pairwise values must be finite and positive.")
    if not np.allclose(np.diag(A), 1) or not np.allclose(A * A.T, 1):
        raise ValueError(
            "Pairwise matrix must have a unit diagonal and reciprocal values."
        )
    n = A.shape[0]

    if A.shape[0] != A.shape[1]:
        raise ValueError("Pairwise matrix must be square.")

    # ── Step 1: Normalise columns
    col_sums = A.sum(axis=0)
    A_norm = A / col_sums

    # ── Step 2: Priority vector
    weights = A_norm.mean(axis=1)

    # ── Step 3: Consistency
    Aw = A @ weights
    lambda_vec = Aw / weights
    lambda_max = float(lambda_vec.mean())

    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = _RI.get(n, 1.49)
    cr = ci / ri if ri > 0 else 0.0

    is_valid = cr < 0.10

    logger.debug(
        "AHP: n=%s, λ_max=%.4f, CI=%.4f, CR=%.4f, valid=%s",
        n,
        lambda_max,
        ci,
        cr,
        is_valid,
    )

    return {
        "weights": weights.tolist(),
        "lambda_max": lambda_max,
        "consistency_index": ci,
        "consistency_ratio": cr,
        "is_valid": is_valid,
    }


def build_reciprocal_matrix(
    upper_values: dict[tuple[int, int], float], n: int
) -> list[list[float]]:
    """
    Build a full n×n reciprocal matrix from upper-triangle values.

    Args:
        upper_values: {(i, j): value} for i < j
        n: dimension

    Returns:
        n×n list of floats
    """
    A = [[1.0] * n for _ in range(n)]
    for (i, j), v in upper_values.items():
        A[i][j] = v
        A[j][i] = 1.0 / v
    return A
