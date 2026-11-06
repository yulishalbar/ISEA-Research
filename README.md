# AI-Assisted Sustainable Supplier Selection

## Working prototype: UF produce suppliers

The current implementation narrows the proposal below to ingredient suppliers,
starting with **leafy greens**. Research question: **How can a weighted scoring
model help a university dining operation compare food suppliers based on cost,
sustainability, local sourcing, and product quality?** Availability is included
as a fifth criterion. The app does not yet implement AI document extraction.

### Run locally (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local address printed by Streamlit. Edit the supplier table and weights
in the browser; each edit automatically recalculates the results. No manual Python
rerun is needed while the server is running. Download the Excel report to preserve
edits; browser edits do not overwrite the source CSV. This is a local app, not a
deployed service, and it does not watch changes to external Excel files.

### Data and scoring

`data/suppliers.csv` contains **five eligible fictional suppliers and one excluded
fictional record**, all offering leafy greens. Every value is simulated; none
represents a real supplier, quote, or verified UF purchasing record. A real ranking
requires comparable offers and documented evidence. Do not mix real observations
and simulated assumptions without explicitly identifying them in each row.

| Field | Definition |
|---|---|
| supplier / ingredient | Unique supplier-product pair; use a common product specification |
| eligible | True only after a reviewer verifies food safety, capacity, delivery and other minimum requirements |
| price_per_lb | Positive delivered USD/lb for the same grade, volume, packaging and quote period |
| quality | 0–100 acceptance percentage using the same documented inspection protocol |
| local_share | 0–100 percentage of offered product grown in Florida (project definition of local) |
| sustainability | 0–100 evidence score using the rubric below |
| availability | 0–100 percentage of required delivery weeks covered |
| data_type | Simulated, observed, or mixed; explain assumptions in evidence |
| evidence | Source URL or record ID, observation/quote date, specification, rubric reasoning and limitations |

Suggested sustainability rubric: score emissions and food waste separately,
each at 0 (documented absence of a program), 25 (documented measurement), or 50
(measurement plus a documented reduction plan with targets), then sum. Unavailable
evidence is **missing**, not zero. This measures documented practices, not verified
environmental impact, and is a researcher-designed rubric rather than UF policy.

Default weights: price 30%, quality 25%, local sourcing 20%, sustainability 15%,
availability 10%. These are illustrative assumptions balancing affordability and
operational suitability (55%) with local/environmental priorities (35%) and supply
coverage (10%). They are not estimated from survey percentages or endorsed by UF.
Use stakeholder input and sensitivity analysis to justify final research weights.

Price score = `100 × lowest price among ranked suppliers / supplier price`.
Other criteria already use a common 0–100 scale. Total score is the weighted sum.
Weights must lie between 0 and 1 and sum to 1. Equal scores share rank; alphabetical
ordering within a tie is only for display. Scores depend on the comparison set,
including its minimum price, and are not universal supplier ratings.

Missing values on positive-weight criteria exclude a supplier, with a reason in
the audit table. Missing zero-weight criteria are allowed. If price is unavailable,
set its weight to zero and explicitly redistribute it across other criteria.
No per-supplier reweighting or imputation occurs. Sustainability sensitivity sweeps
0–100% in 1 percentage point increments, preserving other weight ratios. It shows
leader changes, ties, and comparison-set size; endpoint changes can admit suppliers
missing an inactive criterion. It does not calculate exact analytical thresholds.

Import CSV with the schema above, or an `.xlsx` workbook with a `Suppliers` sheet
and optional `Weights` sheet (`criterion`, `weight`, decimals summing to 1).
Export includes those sheets plus `Ranking`, `Audit`, `Sensitivity`, and `Notes`.
Reloading the export restores supplier inputs and weights. Supply provenance for
each metric within `evidence`; the app checks format and ranges, not factual truth.

### Research basis and next data collection

- [UF Dining Services Management solicitation (2021)](https://procurement.ufl.edu/wp-content/uploads/2021/07/ITN22NH-100-Dining-Service-Management.pdf), section 1.2, PDF pages 6–8: program priorities inform the selection of criteria.
- [UF Food Service Master Plan (2019)](https://businessservices.ufl.edu/wp-content/uploads/2020/01/Food-Svcs-Master-Plan-Report_Final_December-2019.pdf): background for affordability, local sourcing and food-waste priorities.

These historical documents establish research context, not current supplier prices,
performance, or official weights. Request existing releasable quotes/purchasing
records for one leafy-green specification from UF Business Services or the dining
contract administrator: supplier, product/grade, quote dates, delivered unit price,
pack size, volumes, origin, delivery coverage, quality acceptance records, and
environmental evidence. Obtain at least five comparable offers before claiming a
real supplier comparison. No outreach has been sent as part of this prototype.

### Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover priority-driven ranking changes, price normalization, ties, missing
data, invalid inputs, and sensitivity scenarios. The broader proposal below remains
as background; the implemented scope is the prototype described above.

## Project Overview

Supplier selection is a multi-criteria decision: organizations must balance cost, quality, delivery reliability, and risk with environmental and social responsibilities. This project proposes a decision-support tool that combines transparent multi-criteria decision analysis with AI-assisted review of supplier information.

The tool will organize supplier data, score suppliers against selected sustainability and operational criteria, and explain how each criterion contributes to the final ranking. AI may help extract or summarize evidence from supplier documents, but the scoring rules and evidence should remain reviewable by a human decision-maker. The project is a research prototype, not an automated procurement system or a certification of supplier claims.

## Research Question

**How can AI-assisted analysis and transparent multi-criteria decision methods support sustainable supplier selection while keeping the resulting rankings explainable and subject to human review?**

Supporting questions:

- How do supplier rankings change when sustainability criteria are included alongside conventional cost, quality, and delivery criteria?
- Can AI-assisted extraction make supplier evidence easier to compare without obscuring its source or uncertainty?
- What trade-offs and limitations should decision-makers consider when using the resulting ranking?

## Why This Project Matters

Purchasing decisions can influence environmental impacts, labor practices, supply-chain resilience, and organizational costs. Yet supplier information is often inconsistent, incomplete, and difficult to compare. Sustainability claims may be expressed in different formats or supported by evidence of varying quality.

A structured decision-support approach can make trade-offs more visible and help teams apply criteria consistently. This project emphasizes traceability and human review so that an AI-generated summary is treated as supporting evidence—not as a verified fact or a substitute for due diligence.

## How It Relates to Industrial and Systems Engineering (ISE)

Supplier selection is an ISE problem because it involves designing and evaluating a system of interacting objectives, constraints, stakeholders, and processes. The project applies ISE concepts by:

- Modeling supplier selection as a multi-criteria decision problem.
- Examining trade-offs between cost, quality, delivery, risk, and sustainability.
- Using data and decision analysis to compare alternatives consistently.
- Considering the procurement workflow and the people responsible for reviewing decisions.
- Evaluating transparency, sensitivity to criteria weights, and the limitations of available data.

## Proposed Method

1. **Define the decision context.** Select a product or service category for a small research case study and identify the decision criteria and stakeholders.
2. **Establish criteria and measures.** Develop a documented set of operational, environmental, and social criteria. Possible measures include total cost, quality, delivery performance, emissions information, environmental certifications, and labor-practice disclosures. Criteria should be selected based on data availability and the case-study scope.
3. **Prepare supplier data.** Assemble a small, clearly documented dataset using publicly available, synthetic, or otherwise authorized information. Record the source, date, and limitations of each data point.
4. **Build a transparent baseline.** Normalize the available measures and use a weighted-sum scoring method to produce a baseline ranking. Document the criteria weights and explain how they were chosen.
5. **Add AI-assisted evidence review.** If supplier documents are available, use an AI-assisted workflow to extract or summarize evidence for selected criteria. Keep links or references to source passages, distinguish missing information from negative performance, and require human verification before using extracted information in a score.
6. **Compare and test the results.** Compare rankings with and without sustainability criteria and, where feasible, compare AI-assisted evidence entry with manual review. Perform sensitivity analysis to see whether reasonable changes in criteria weights or uncertain values change the ranking.
7. **Interpret findings and limitations.** Discuss trade-offs, data quality, uncertainty, potential bias, and appropriate human oversight. Avoid presenting a ranking as universally valid.

The exact criteria, data source, and AI workflow will depend on the selected case study. Any AI-generated output should be labeled and checked against its source before being treated as research data.

## 5-Week Timeline

| Week | Activities | Milestone |
|---|---|---|
| 1 | Review relevant research; choose the case-study scope; define the research question and candidate criteria. | Approved scope and initial criteria |
| 2 | Identify an appropriate data source; collect and document supplier data; define scoring and normalization rules. | Documented dataset and baseline design |
| 3 | Implement the baseline scoring model and produce an initial supplier comparison. | Working baseline ranking |
| 4 | Add the scoped AI-assisted evidence workflow; verify extracted information; run ranking comparisons and sensitivity analysis. | AI-assisted prototype and analysis |
| 5 | Interpret results and limitations; complete the report, code, and presentation materials. | Final research deliverables |

## Expected Deliverables

- **Research report** describing the problem, related work, method, results, and limitations.
- **Documented dataset** with sources, definitions, and notes on missing or uncertain information, subject to source permissions.
- **Prototype code** for data preparation, scoring, ranking, and (if in scope) AI-assisted evidence review.
- **Reproducible analysis** comparing rankings and showing sensitivity to criteria weights or uncertain data.
- **Presentation** summarizing the research question, approach, findings, and practical implications.

## Scope and Responsible Use

This project is intended for educational and research use. Supplier scores are decision-support outputs, not definitive judgments about a supplier. Results depend on the selected criteria, weights, data quality, and case-study assumptions. Human reviewers should verify evidence, consider context, and make the final decision.
