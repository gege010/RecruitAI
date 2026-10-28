"""
Ensemble aggregator — Borda Count method.

Each algorithm contributes an ordinal rank per candidate.
Final score = sum of ranks (lower is better → ascending sort gives winner).
"""

from __future__ import annotations

import pandas as pd


def run_ensemble(scores: dict[str, pd.Series]) -> pd.DataFrame:
    """
    Aggregate multiple MCDM scoring series via Borda Count.

    Args:
        scores: dict of {algo_name: pd.Series(score, index=candidate_ids)}
                Higher score = better for each algorithm.

    Returns:
        DataFrame with columns:
            candidate_id, <algo>_score, <algo>_rank, borda_score, ensemble_rank
    """
    df = pd.DataFrame(scores)

    # Rank each algorithm (ascending rank = best score first)
    for algo, series in scores.items():
        df[f"{algo}_rank"] = series.rank(ascending=False, method="min").astype(int)

    rank_cols = [f"{algo}_rank" for algo in scores]
    df["borda_score"] = df[rank_cols].sum(axis=1)
    df["ensemble_rank"] = (
        df["borda_score"].rank(ascending=True, method="min").astype(int)
    )

    # Rename score columns
    df = df.rename(columns={algo: f"{algo}_score" for algo in scores})

    df.index.name = "candidate_id"
    return df.reset_index().sort_values("ensemble_rank")
