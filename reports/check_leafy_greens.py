from pathlib import Path
import json
import pandas as pd
from scoring import CRITERIA, DEFAULT_WEIGHTS, REQUIRED, rank_suppliers, sensitivity, validate

source = Path(r'C:\Users\yulis\Downloads\leafy-greens-supplier-data (1).xlsx')
sheets = pd.read_excel(source, sheet_name=None)
public = pd.DataFrame(json.loads(Path('reports/leafy-greens-public-evidence.json').read_text(encoding='utf-8')))
rows = []
for _, row in sheets['Summary'].iterrows():
    evidence = '; '.join(f'{k}: {v}' for k, v in row.items() if k != 'Supplier' and pd.notna(v))
    findings = public[public.supplier.eq(row['Supplier'])]
    updates = ' | '.join(f"{r.field}: {r.finding} Source: {r.source_url} (accessed {r.accessed})" for r in findings.itertuples())
    rows.append(dict(supplier=row['Supplier'], ingredient='Leafy greens', eligible=False,
                     **{c: float('nan') for c in CRITERIA}, data_type='observed',
                     evidence=f'Current source checks supersede conflicting original notes: {updates} | Original workbook notes (historical, not independently verified): {evidence}. Numeric measurements unavailable; eligibility unverified.'))
data = pd.DataFrame(rows)
checks = []
def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})
    assert condition, name

check('Original workbook requires conversion: no Suppliers sheet', 'Suppliers' not in sheets)
check('All eight supplier records preserved', len(data) == len(sheets['Summary']) == 8)
validated = validate(data, DEFAULT_WEIGHTS)
check('Converted supplier schema validates', set(REQUIRED).issubset(validated.columns))
ranked, audit = rank_suppliers(data, DEFAULT_WEIGHTS, 'Leafy greens')
check('Unverified suppliers are excluded', ranked.empty and audit.status.eq('Requirements not verified').all())
probe = data.copy()
probe['eligible'] = True  # Test-only probe; does not change saved eligibility.
probe_ranked, probe_audit = rank_suppliers(probe, DEFAULT_WEIGHTS, 'Leafy greens')
check('Missing numeric evidence prevents ranking even if eligibility were confirmed', probe_ranked.empty and probe_audit.status.str.startswith('Missing:').all())
sweep = sensitivity(data, DEFAULT_WEIGHTS, 'Leafy greens')
check('All 101 sensitivity scenarios run without unsupported rankings', len(sweep) == 101 and sweep.ranked_count.eq(0).all())
output = Path('reports/leafy-greens-import-ready.xlsx')
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    data.to_excel(writer, sheet_name='Suppliers', index=False)
    pd.DataFrame(DEFAULT_WEIGHTS.items(), columns=['criterion', 'weight']).to_excel(writer, sheet_name='Weights', index=False)
    audit.to_excel(writer, sheet_name='Audit', index=False)
    sweep.to_excel(writer, sheet_name='Sensitivity', index=False)
    public.to_excel(writer, sheet_name='Public evidence', index=False)
    for name, frame in sheets.items():
        frame.to_excel(writer, sheet_name=name, index=False)
loaded = pd.read_excel(output, sheet_name='Suppliers')
roundtrip, _ = rank_suppliers(loaded, DEFAULT_WEIGHTS, 'Leafy greens')
check('Saved Excel reimports and remains unranked', len(loaded) == 8 and roundtrip.empty)
pd.DataFrame(checks).to_csv('reports/leafy-greens-checks.csv', index=False)
report = [
    '# Excel data checks and public research',
    'Research accessed November 6, 2026. Source workbook: ' + str(source),
    f'{len(checks)}/{len(checks)} workbook checks passed. Eight supplier records preserved. 101 sensitivity scenarios completed; zero eligible ranked suppliers.',
    'The app-ready workbook now includes a Public evidence sheet and source-linked updates in each supplier evidence field. Original sheets are preserved as historical input; new findings supersede conflicting notes. Public website statements are not independent audits.',
    'All five numeric criteria remain blank: no comparable delivered supplier quotes, common inspection acceptance rates, offered-product Florida shares, emissions-plus-food-waste rubric measurements, or committed delivery-week coverage were established in the sources reviewed. Eligibility remains false pending food-safety, capacity and delivery verification. Default weights are illustrative app assumptions.',
    'A Florida address does not prove a 100% Florida share of an offer; year-round production does not guarantee 100% of required deliveries. Water conservation and organic claims cannot substitute for the existing sustainability rubric. Mixed CSA prices and historical market benchmarks are not supplier lettuce quotes.',
    '## Source findings',
]
for r in public.itertuples():
    report.append(f'- **{r.supplier} ? {r.field}:** {r.finding} [Source]({r.source_url}) (accessed {r.accessed}).')
report.extend([
    '## Remaining records needed',
    'For one common leafy-green specification, obtain product/grade, packaging and net pounds, order volume, quote validity, delivered Gainesville price, grower/lot origin, inspection accepted/inspected totals, required and committed delivery weeks, current food-safety audit scope/expiry, and emissions/food-waste evidence with dates. Request these records through the contacts above. No messages or forms have been submitted.',
    'To reproduce workbook checks: `.\\.venv\\Scripts\\python.exe -m reports.check_leafy_greens`. This uses the original Downloads workbook and the saved public-evidence JSON; it does not refresh web research.',
])
Path('reports/leafy-greens-results.md').write_text('\n\n'.join(report) + '\n', encoding='utf-8')
print(json.dumps(checks, indent=2))
print('Created', output)
