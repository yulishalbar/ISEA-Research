from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from scoring import CRITERIA, DEFAULT_WEIGHTS, rank_suppliers, sensitivity, validate

st.set_page_config(page_title="UF Produce Supplier Lab", layout="wide")
st.title("UF Produce Supplier Lab")
st.warning("Research prototype. Included suppliers and measurements are fictional. Results are scenario recommendations, not UF purchasing advice.")
st.write("Choose an ingredient, review supplier evidence, and adjust priorities. Rankings update automatically after each edit.")

uploaded = st.file_uploader("Import supplier CSV or Excel workbook", type=["csv", "xlsx"])
weights = DEFAULT_WEIGHTS.copy()
try:
    if uploaded:
        if uploaded.name.lower().endswith(".xlsx"):
            sheets = pd.read_excel(uploaded, sheet_name=None)
            data = sheets["Suppliers"]
            if "Weights" in sheets:
                table = sheets["Weights"]
                if table.criterion.duplicated().any():
                    raise ValueError("Duplicate criteria in Weights sheet.")
                weights = dict(zip(table.criterion, table.weight))
        else:
            data = pd.read_csv(uploaded)
    else:
        data = pd.read_csv(Path(__file__).parent / "data" / "suppliers.csv")
    data = validate(data, weights)
except (ValueError, KeyError, TypeError, OSError) as exc:
    st.error(f"Cannot load data: {exc}")
    st.stop()

with st.expander("Scoring rules and data definitions"):
    st.markdown("""
    All offers must refer to the **same ingredient, specification, delivered USD/lb,
    quantity, and quote period**. Confirm food safety, capacity, delivery, and other
    minimum requirements before marking `eligible=True`. Eligibility is a manual gate.

    - **Price:** 100 × lowest comparable eligible complete quote / supplier quote.
    - **Quality:** acceptance percentage from a documented common inspection protocol.
    - **Local share:** percentage of the offered product grown in Florida; this is a project definition.
    - **Sustainability:** common evidence rubric: 0–50 points for emissions measurement/reduction
      and 0–50 for food-waste measurement/reduction (see README).
    - **Availability:** percentage of required delivery weeks the offer can fulfill.

    Total = sum of each 0–100 score × its weight. Weights must sum to 100%.
    Missing active criteria exclude a supplier; zero-weight criteria may be blank.
    To study a scenario without cost, set price to 0% and redistribute that weight.
    No missing values are guessed, and weights are never changed per supplier.
    Ties share rank. Keep provenance, date, and rubric details in `evidence`.
    """)

st.subheader("Supplier data")
st.caption("Edits stay in this browser session. Download a workbook to save them. Add rows using the table’s final row.")
edited = st.data_editor(data, num_rows="dynamic", hide_index=True, key=f"data_{uploaded.file_id if uploaded else 'demo'}")
ingredient = st.selectbox("Ingredient", sorted(edited.ingredient.dropna().astype(str).unique()))
st.subheader("Criteria weights")
st.caption("Starting weights are illustrative research assumptions, not official UF weights.")
cols = st.columns(len(CRITERIA))
chosen = {c: cols[i].number_input(c.replace("_", " ").title() + " (%)", min_value=0.0, max_value=100.0,
                                value=float(weights[c] * 100), step=1.0,
                                key=f"weight_{c}_{uploaded.file_id if uploaded else 'demo'}") / 100
          for i, c in enumerate(CRITERIA)}
st.write(f"Total weight: {sum(chosen.values()):.0%}")
try:
    ranked, audit = rank_suppliers(edited, chosen, ingredient)
except (ValueError, TypeError) as exc:
    st.error(str(exc))
    st.stop()

st.subheader("Scenario results")
if ranked.empty:
    st.info("No suppliers can be ranked. Check eligibility and missing active criteria below.")
else:
    winners = ranked[ranked["rank"].eq(1)]
    st.success("Highest scoring: " + ", ".join(winners.supplier) + f" ({winners.score.iloc[0]:.2f}/100)")
    st.dataframe(ranked[["rank", "supplier", "score", "data_type", *[f"{c}_points" for c in CRITERIA]]], hide_index=True)
    st.bar_chart(ranked.set_index("supplier")[[f"{c}_points" for c in CRITERIA]])
    st.caption("Each segment is the criterion’s contribution to the total. Rankings use full precision.")
    if len(ranked) > 1:
        top, second = ranked.iloc[0], ranked.iloc[1]
        differences = {c: top[f"{c}_points"] - second[f"{c}_points"] for c in CRITERIA}
        st.write(f"{top.supplier} scores {top.score - second.score:.2f} points above {second.supplier}.")
        st.write("Contribution differences: " + "; ".join(f"{c}: {delta:+.2f}" for c, delta in differences.items()))
st.dataframe(audit[["supplier", "status", "data_type", "evidence"]], hide_index=True)

st.subheader("Sustainability sensitivity")
st.caption("Sweep from 0% to 100% in 1% steps, preserving the ratios of other weights. Endpoint scenarios may admit suppliers with missing zero-weight criteria; compare ranked_count. This is a sampled analysis, not an exact crossover calculation.")
sweep = sensitivity(edited, chosen, ingredient)
if sweep.empty:
    st.info("Give another criterion positive weight to define its ratio during this sweep.")
else:
    changes = sweep.leaders.ne(sweep.leaders.shift()) | sweep.ranked_count.ne(sweep.ranked_count.shift())
    st.dataframe(sweep[changes], hide_index=True)
    st.download_button("Download full sensitivity CSV", sweep.to_csv(index=False), "sensitivity.csv", "text/csv")

buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    edited.to_excel(writer, sheet_name="Suppliers", index=False)
    pd.DataFrame(chosen.items(), columns=["criterion", "weight"]).to_excel(writer, sheet_name="Weights", index=False)
    ranked.to_excel(writer, sheet_name="Ranking", index=False)
    audit.to_excel(writer, sheet_name="Audit", index=False)
    sweep.to_excel(writer, sheet_name="Sensitivity", index=False)
    pd.DataFrame({"notes": ["Research prototype; demo values are fictional.", "Weights are researcher assumptions, not official UF policy.", "See README for scoring rules. Save evidence and quote dates before real use."]}).to_excel(writer, sheet_name="Notes", index=False)
st.download_button("Save data, weights, and report as Excel", buffer.getvalue(), "supplier_comparison.xlsx",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
st.caption("Research basis: UF dining solicitation (2021), section 1.2, and Food Service Master Plan (2019). Historical priorities do not establish current supplier performance or official criterion weights.")
