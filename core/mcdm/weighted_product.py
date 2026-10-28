"""
Weighted Product (WP) method.

  score_i = Π (x_ij ^ w_j)       (all criteria treated as benefit)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from core.mcdm.validation import validate_inputs


def run_wp(
    decision_matrix: pd.DataFrame,
    weights: list[float],
) -> pd.Series:
    """
    Compute Weighted Product scores.

    Args:
        decision_matrix: rows = candidates, columns = criteria.
        weights: weight vector (will be normalised internally).

    Returns:
        pd.Series of scores indexed like decision_matrix.
    """
    dm, w = validate_inputs(decision_matrix, weights)

    # Avoid log(0): clip to small positive value
    dm = np.clip(dm, 1e-9, None)

    log_scores = (np.log(dm) * w).sum(axis=1)
    scores = np.exp(log_scores)

    # Normalise to [0, 1] for comparability
    s_min, s_max = scores.min(), scores.max()
    if s_max > s_min:
        scores = (scores - s_min) / (s_max - s_min)

    return pd.Series(scores, index=decision_matrix.index, name="WP")
