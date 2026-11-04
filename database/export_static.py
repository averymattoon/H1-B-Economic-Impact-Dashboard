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

# COVID trends, summed to whole industries and whole states. Only groups with at least
# MIN_2019 applications in FY2019 are kept, so tiny industry-state cells (e.g. 300 -> 1)
# don't dominate the "largest declines" charts. Each row has a level of 'industry' or 'state'.
MIN_2019 = 1000
write('covid_trends.json', rows(f"""
    WITH ind AS (
      SELECT 'industry' AS level, n.industry_name AS name,
             SUM(c.app_count_2019) AS app_count_2019, SUM(c.app_count_2020) AS app_count_2020,
             SUM(c.app_count_2021) AS app_count_2021
      FROM mv_covid_trend_analysis c
      JOIN naics_lookup n ON c.industry = n.naics_code
      GROUP BY n.industry_name
    ),
    st AS (
      SELECT 'state' AS level, worksite_state AS name,
             SUM(app_count_2019) AS app_count_2019, SUM(app_count_2020) AS app_count_2020,
             SUM(app_count_2021) AS app_count_2021
      FROM mv_covid_trend_analysis
      WHERE worksite_state IS NOT NULL
      GROUP BY worksite_state
    ),
    allrows AS (SELECT * FROM ind UNION ALL SELECT * FROM st)
    SELECT level, name, app_count_2019, app_count_2020, app_count_2021,
           ROUND(100.0 * (app_count_2020 - app_count_2019) / app_count_2019, 2) AS pct_change_2019_2020,
           ROUND(100.0 * (app_count_2021 - app_count_2019) / app_count_2019, 2) AS pct_change_2019_2021
    FROM allrows
    WHERE app_count_2019 >= {MIN_2019}
    ORDER BY level, pct_change_2019_2020
"""))

# Sanity check printed to the terminal: national totals per year
cur.execute("SELECT fiscal_year, COUNT(*) AS n FROM applications "
            "WHERE fiscal_year BETWEEN 2018 AND 2022 GROUP BY 1 ORDER BY 1")
print('Applications per fiscal year:', {r['fiscal_year']: r['n'] for r in cur.fetchall()})

write('exposure_scores.json', {
    'industries': rows('SELECT * FROM mv_exposure_score_industry ORDER BY exposure_score DESC'),
    'states': rows('SELECT * FROM mv_exposure_score_state ORDER BY exposure_score DESC'),
})

conn.close()
print('Done.')
