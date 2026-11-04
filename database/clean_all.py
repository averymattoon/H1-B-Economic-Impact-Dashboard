"""
Clean every raw H-1B disclosure file in this folder with data_cleaning.py,
naming each output so load_data_fast.py can find it by year:
  full years -> cleaned_h1b_2016.csv
  quarters   -> cleaned_h1b_2023q1.csv
Skips any output that already exists, so it is safe to rerun.

Usage (from the folder that holds the raw .xlsx files and data_cleaning.py):
  python3 clean_all.py
"""
import re
import sys
from pathlib import Path

import pandas as pd
from data_cleaning import clean_h1b_dataset

folder = Path('.')
raw_files = sorted(p for p in folder.glob('*.xlsx') if not p.name.startswith('~$'))

def output_name(name: str):
    # Fiscal year: "FY2013", "FY16", "FY14" ...
    m = re.search(r'FY_?(\d{4}|\d{2})(?!\d)', name, re.I)
    if not m:
        return None
    year = m.group(1)
    year = int(year) if len(year) == 4 else 2000 + int(year)
    # Quarter only matters from FY2020 on (earlier "Q4" files are full-year)
    q = re.search(r'_Q([1-4])', name, re.I)
    suffix = f'q{q.group(1)}' if (q and year >= 2020) else ''
    # FY2009 comes from two filing systems; give each its own output file
    if year == 2009:
        suffix = 'b' if 'icert' in name.lower() else 'a'
    return year, f'cleaned_h1b_{year}{suffix}.csv'

for p in raw_files:
    parsed = output_name(p.name)
    if parsed is None:
        print(f'SKIP (no fiscal year in name): {p.name}')
        continue
    year, out = parsed
    if year < 2009 or year > 2024:
        print(f'SKIP (outside 2009-2024): {p.name}')
        continue
    if Path(out).exists():
        print(f'SKIP (already cleaned): {p.name} -> {out}')
        continue
    print(f'\n=== {p.name} -> {out} ===')
    try:
        clean_h1b_dataset(str(p), out)
    except Exception as e:
        print(f'FAILED on {p.name}: {e}', file=sys.stderr)

# Quick check: wage units and fiscal years in every cleaned file.
# Units must be ones load_data_fast.py understands (Hour, Week, Bi-Weekly, Month, Year),
# otherwise those wages are treated as annual.
print('\n=== Check: rows, fiscal years and wage units per cleaned file ===')
for c in sorted(folder.glob('cleaned_h1b_*.csv')):
    df = pd.read_csv(c, usecols=lambda col: col in ('fiscal_year', 'wage_unit'), low_memory=False)
    years = sorted(df['fiscal_year'].dropna().astype(int).unique().tolist()) if 'fiscal_year' in df else '?'
    units = df['wage_unit'].value_counts().to_dict() if 'wage_unit' in df else 'no wage_unit column'
    print(f'{c.name}: {len(df):,} rows | fiscal years {years} | units {units}')
