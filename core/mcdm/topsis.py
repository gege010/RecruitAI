"""
TOPSIS — Technique for Order of Preference by Similarity to Ideal Solution.

Steps:
  1. Normalize decision matrix (vector normalization).
  2. Apply weights.
  3. Compute ideal-best (A+) and ideal-worst (A-).
  4. Compute distances d+ and d-.
  5. score_i = d- / (d+ + d-)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from core.mcdm.validation import validate_inputs


def run_topsis(
    decision_matrix: pd.DataFrame,
    weights: list[float],
) -> pd.Series:
    """
    Compute TOPSIS closeness coefficient.

    Args:
        decision_matrix: rows = candidates, columns = criteria (all benefit).
        weights: weight vector (will be normalised internally).

    Returns:
        pd.Series of scores in [0,1] indexed like decision_matrix.
        Higher score = closer to ideal.
    """
    dm, w = validate_inputs(decision_matrix, weights)

    # ── 1. Vector normalization
    norms = np.sqrt((dm**2).sum(axis=0))
    norms = np.where(norms == 0, 1, norms)
    r = dm / norms

    # ── 2. Weighted normalized matrix
    v = r * w

    # ── 3. Ideal solutions (all benefit → max is best)
    a_pos = v.max(axis=0)  # A+
    a_neg = v.min(axis=0)  # A-

    # ── 4. Euclidean distances
    d_pos = np.sqrt(((v - a_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((v - a_neg) ** 2).sum(axis=1))

    # ── 5. Closeness coefficient
    denom = d_pos + d_neg
    # Identical alternatives have no distance preference, not zero quality.
    scores = np.divide(d_neg, denom, out=np.full_like(denom, 0.5), where=denom > 0)

    return pd.Series(scores, index=decision_matrix.index, name="TOPSIS")
