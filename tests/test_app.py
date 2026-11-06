import unittest
from io import BytesIO
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_initial_render_weight_validation_and_export(self):
        app = AppTest.from_file(str(Path(__file__).parents[1] / "app.py")).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.success), 1)
        app.number_input[0].set_value(0).run()
        self.assertTrue(any("sum to 1" in error.value for error in app.error))
        app.number_input[1].set_value(55).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.success), 1)

    def test_excel_roundtrip(self):
        from scoring import DEFAULT_WEIGHTS, rank_suppliers
        data = pd.read_csv(Path(__file__).parents[1] / "data/suppliers.csv")
        stream = BytesIO()
        with pd.ExcelWriter(stream, engine="openpyxl") as writer:
            data.to_excel(writer, sheet_name="Suppliers", index=False)
            pd.DataFrame(DEFAULT_WEIGHTS.items(), columns=["criterion", "weight"]).to_excel(writer, sheet_name="Weights", index=False)
        sheets = pd.read_excel(BytesIO(stream.getvalue()), sheet_name=None)
        weights = dict(zip(sheets["Weights"].criterion, sheets["Weights"].weight))
        ranked, _ = rank_suppliers(sheets["Suppliers"], weights, "Leafy greens")
        self.assertEqual(len(ranked), 5)
