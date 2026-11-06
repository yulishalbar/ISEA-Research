import unittest
from pathlib import Path

import pandas as pd

from scoring import CRITERIA, DEFAULT_WEIGHTS, rank_suppliers, sensitivity


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.read_csv(Path(__file__).parents[1] / "data/suppliers.csv")

    def test_price_only_and_sustainability_only(self):
        for criterion, expected in [("price_per_lb", "Demo Budget Greens"), ("sustainability", "Demo Circular Farm")]:
            weights = {c: float(c == criterion) for c in CRITERIA}
            ranked, _ = rank_suppliers(self.data, weights, "Leafy greens")
            self.assertEqual(ranked.iloc[0].supplier, expected)
            self.assertEqual(ranked.iloc[0].score, 100 if criterion == "price_per_lb" else 98)

    def test_missing_active_excluded_and_inactive_allowed(self):
        self.data.loc[0, "price_per_lb"] = float("nan")
        ranked, audit = rank_suppliers(self.data, DEFAULT_WEIGHTS, "Leafy greens")
        self.assertNotIn("Demo Budget Greens", ranked.supplier.tolist())
        self.assertIn("price_per_lb", audit.iloc[0].status)
        weights = dict.fromkeys(CRITERIA, 0.0)
        weights["quality"] = 1.0
        ranked, _ = rank_suppliers(self.data, weights, "Leafy greens")
        self.assertIn("Demo Budget Greens", ranked.supplier.tolist())

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            rank_suppliers(self.data, dict.fromkeys(CRITERIA, 0), "Leafy greens")
        self.data.loc[0, "quality"] = 101
        with self.assertRaises(ValueError):
            rank_suppliers(self.data, DEFAULT_WEIGHTS, "Leafy greens")

    def test_ties_and_weighted_sum(self):
        baseline, _ = rank_suppliers(self.data, DEFAULT_WEIGHTS, "Leafy greens")
        budget = baseline[baseline.supplier.eq("Demo Budget Greens")].iloc[0]
        self.assertAlmostEqual(budget.score, 30 + 75 * .25 + 20 * .20 + 35 * .15 + 95 * .10)
        self.data.loc[1, list(CRITERIA)] = self.data.loc[0, list(CRITERIA)].values
        ranked, _ = rank_suppliers(self.data, {c: float(c == "price_per_lb") for c in CRITERIA}, "Leafy greens")
        self.assertEqual((ranked["rank"] == 1).sum(), 2)
        self.assertEqual(ranked.iloc[0].score, 100)

    def test_sensitivity_and_empty_selection(self):
        sweep = sensitivity(self.data, DEFAULT_WEIGHTS, "Leafy greens")
        self.assertEqual(len(sweep), 101)
        self.assertEqual(sweep.iloc[-1].leaders, "Demo Circular Farm")
        ranked, _ = rank_suppliers(self.data, DEFAULT_WEIGHTS, "Tomatoes")
        self.assertTrue(ranked.empty)


if __name__ == "__main__":
    unittest.main()
