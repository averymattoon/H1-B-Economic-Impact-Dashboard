"""
Export the dashboard's summary views from Postgres to static JSON files, so the
deployed dashboard needs no database.

Run from the database/ folder (uses the same .env as the loaders):
  python3 export_static.py
Writes to ../frontend/data/.
"""
import json
import os
from decimal import Decimal
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

OUT = Path('../frontend/data')
EMPLOYER_TOP_N = 50  # the dashboard requests the top 50 employers

load_dotenv()
conn = psycopg2.connect(host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT', 5432),
                        database=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
                        password=os.getenv('DB_PASSWORD'))
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def clean(v):
    if isinstance(v, Decimal):
        f = float(v)
        return int(f) if f.is_integer() else round(f, 2)
    if isinstance(v, float):
        return round(v, 2)
    return v


def rows(sql):
    cur.execute(sql)
    return [{k: clean(v) for k, v in r.items()} for r in cur.fetchall()]


def write(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(data, separators=(',', ':'), default=str))
    n = len(data) if isinstance(data, list) else sum(len(v) for v in data.values())
    print(f'{path}: {n:,} rows, {path.stat().st_size / 1e6:.1f} MB')


write('industry_metrics.json', rows("""
    SELECT m.industry, COALESCE(n.industry_name, m.industry) AS industry_name,
           m.total_applications, m.unique_employers, m.avg_annual_wage,
           m.median_annual_wage, m.total_annual_wages, m.fiscal_year
    FROM mv_industry_metrics m
    LEFT JOIN naics_lookup n ON m.industry = n.naics_code
"""))

write('state_metrics.json', rows("""
    SELECT worksite_state, total_applications, unique_employers,
           avg_annual_wage, total_annual_wages, fiscal_year
    FROM mv_state_metrics
"""))

# Employers: keep only what the dashboard can display. For every year, the top N
# employers overall and the top N within each named industry (the industry filter
# only offers industries that have a name in naics_lookup).
write('employer_metrics.json', rows(f"""
    WITH b AS (
      SELECT m.emp_id, m.emp_name, m.industry,
             COALESCE(n.industry_name, m.industry) AS industry_name,
             n.naics_code IS NOT NULL AS named,
             m.total_applications, m.states_covered, m.avg_annual_wage,
             m.median_annual_wage, m.total_annual_wages, m.fiscal_year
      FROM mv_employer_metrics m
      LEFT JOIN naics_lookup n ON m.industry = n.naics_code
    ),
    r AS (
      SELECT b.*,
             ROW_NUMBER() OVER (PARTITION BY fiscal_year ORDER BY total_applications DESC) AS r_year,
             ROW_NUMBER() OVER (PARTITION BY fiscal_year, industry_name ORDER BY total_applications DESC) AS r_ind
      FROM b
    )
    SELECT emp_id, emp_name, industry, industry_name, total_applications, states_covered,
           avg_annual_wage, median_annual_wage, total_annual_wages, fiscal_year
    FROM r
    WHERE r_year <= {EMPLOYER_TOP_N} OR (named AND r_ind <= {EMPLOYER_TOP_N})
"""))

# Same query the old /api/covid-trends route ran (it takes no filters)
write('covid_trends.json', rows("""
    SELECT c.industry, n.industry_name, c.app_count_change_2019_to_2020_pct, c.worksite_state,
           ROUND((c.app_count_2020 - c.app_count_2019)::numeric
                 / NULLIF(c.app_count_2019, 0) * 100, 2) AS pct_change_2019_2020
    FROM mv_covid_trend_analysis c
    LEFT JOIN naics_lookup n ON c.industry = n.naics_code
    WHERE c.app_count_change_2019_to_2020_pct IS NOT NULL
       OR (c.app_count_2019 > 0 AND c.app_count_2020 IS NOT NULL)
    ORDER BY c.app_count_change_2019_to_2020_pct ASC NULLS LAST
    LIMIT 200
"""))

write('exposure_scores.json', {
    'industries': rows('SELECT * FROM mv_exposure_score_industry ORDER BY exposure_score DESC'),
    'states': rows('SELECT * FROM mv_exposure_score_state ORDER BY exposure_score DESC'),
})

conn.close()
print('Done.')
