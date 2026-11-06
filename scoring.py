"""Transparent scoring; no supplier facts are inferred or imputed."""
import math

import pandas as pd

CRITERIA = ("price_per_lb", "quality", "local_share", "sustainability", "availability")
DEFAULT_WEIGHTS = dict(zip(CRITERIA, (0.30, 0.25, 0.20, 0.15, 0.10)))
REQUIRED = ("supplier", "ingredient", "eligible", *CRITERIA, "data_type", "evidence")


def validate(data, weights):
    missing = set(REQUIRED) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")
    if set(weights) != set(CRITERIA):
        raise ValueError("Weights must contain each criterion exactly once.")
    if any(not math.isfinite(float(w)) or not 0 <= w <= 1 for w in weights.values()):
        raise ValueError("Weights must be finite numbers between 0 and 1.")
    if not math.isclose(sum(weights.values()), 1, abs_tol=1e-8):
        raise ValueError("Weights must sum to 1 (100%).")
    result = data.copy()
    for field in ("supplier", "ingredient", "data_type", "evidence"):
        if result[field].isna().any() or result[field].astype(str).str.strip().eq("").any():
            raise ValueError(f"{field} must be filled in for every row.")
        result[field] = result[field].astype(str).str.strip()
    if result.duplicated(["supplier", "ingredient"]).any():
        raise ValueError("Supplier and ingredient pairs must be unique.")
    flags = result.eligible.astype(str).str.lower().str.strip()
    if not flags.isin(["true", "false"]).all():
        raise ValueError("eligible must be True or False; verify requirements before setting True.")
    result["eligible"] = flags.eq("true")
    for criterion in CRITERIA:
        try:
            result[criterion] = pd.to_numeric(result[criterion], errors="raise")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"{criterion} must be numeric or blank.") from exc
        values = result[criterion].dropna()
        if not values.map(math.isfinite).all():
            raise ValueError(f"{criterion} must contain finite values.")
        invalid = values.le(0) if criterion == "price_per_lb" else ~values.between(0, 100)
        if invalid.any():
            raise ValueError(f"{criterion}: prices must be positive; other scores must be 0–100.")
    return result


def rank_suppliers(data, weights, ingredient):
    data = validate(data, weights)
    selected = data[data.ingredient.eq(ingredient)].copy()
    active = [c for c in CRITERIA if weights[c] > 0]
    selected["status"] = selected.apply(
        lambda row: "Requirements not verified" if not row.eligible else
        ("Missing: " + ", ".join(c for c in active if pd.isna(row[c])))
        if any(pd.isna(row[c]) for c in active) else "Ranked", axis=1
    ) if len(selected) else pd.Series(dtype=str)
    ranked = selected[selected.status.eq("Ranked")].copy()
    if ranked.empty:
        return ranked, selected
    # A common comparison set and common weights for every ranked supplier.
    cheapest = ranked.price_per_lb.min() if weights["price_per_lb"] else None
    for criterion in CRITERIA:
        normalized = 100 * cheapest / ranked[criterion] if criterion == "price_per_lb" and cheapest else ranked[criterion]
        ranked[f"{criterion}_points"] = normalized * weights[criterion] if weights[criterion] else 0.0
    ranked["score"] = ranked[[f"{c}_points" for c in CRITERIA]].sum(axis=1)
    ranked["rank"] = ranked.score.rank(method="min", ascending=False).astype(int)
    return ranked.sort_values(["score", "supplier"], ascending=[False, True]), selected


def sensitivity(data, weights, ingredient):
    """Sweep sustainability in 1 percentage point steps; preserve other ratios."""
    rows = []
    other_total = sum(weights[c] for c in CRITERIA if c != "sustainability")
    if other_total == 0:
        return pd.DataFrame()
    for step in range(101):
        share = step / 100
        scenario = {c: (share if c == "sustainability" else weights[c] / other_total * (1 - share)) for c in CRITERIA}
        ranked, _ = rank_suppliers(data, scenario, ingredient)
        winners = ranked[ranked["rank"].eq(1)] if len(ranked) else ranked
        rows.append({"sustainability_weight": share, "leaders": ", ".join(winners.supplier),
                     "score": winners.score.iloc[0] if len(winners) else None,
                     "ranked_count": len(ranked)})
    return pd.DataFrame(rows)
