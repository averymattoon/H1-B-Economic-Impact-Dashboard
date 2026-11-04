-- ============================================================================
-- FEATURE 2: CROSS-PERIOD COVID TREND ANALYSIS
-- ============================================================================
-- Purpose: Compare H-1B activity across pre-COVID (2019), during-COVID (2020),
--          and post-COVID (2021) periods by industry and state
-- ============================================================================

CREATE MATERIALIZED VIEW mv_covid_trend_analysis AS
WITH period_metrics AS (
  SELECT
    e.industry,
    l.worksite_state,
    a.fiscal_year,
    COUNT(*) AS application_count,
    AVG(a.annual_wage) AS avg_wage,
    PERCENTILE_CONT(0.5) 
      WITHIN GROUP (ORDER BY a.annual_wage) AS median_wage,
    SUM(a.annual_wage) AS total_wage_mass
  FROM applications a
  JOIN employers e ON a.emp_id = e.emp_id
  JOIN worksite_locations l ON a.site_id = l.site_id
  WHERE a.fiscal_year IN (2019, 2020, 2021)
  GROUP BY e.industry, l.worksite_state, a.fiscal_year
),
period_comparisons AS (
  SELECT
    industry,
    worksite_state,
    MAX(CASE WHEN fiscal_year = 2019 THEN application_count END) AS app_count_2019,
    MAX(CASE WHEN fiscal_year = 2019 THEN avg_wage END) AS avg_wage_2019,
    MAX(CASE WHEN fiscal_year = 2019 THEN median_wage END) AS median_wage_2019,
    MAX(CASE WHEN fiscal_year = 2020 THEN application_count END) AS app_count_2020,
    MAX(CASE WHEN fiscal_year = 2020 THEN avg_wage END) AS avg_wage_2020,
    MAX(CASE WHEN fiscal_year = 2020 THEN median_wage END) AS median_wage_2020,
    MAX(CASE WHEN fiscal_year = 2021 THEN application_count END) AS app_count_2021,
    MAX(CASE WHEN fiscal_year = 2021 THEN avg_wage END) AS avg_wage_2021,
    MAX(CASE WHEN fiscal_year = 2021 THEN median_wage END) AS median_wage_2021
  FROM period_metrics
  GROUP BY industry, worksite_state
)
SELECT
  industry,
  worksite_state,
  app_count_2019,
  app_count_2020,
  app_count_2021,
  ROUND(
    (100.0 * (app_count_2020 - app_count_2019) / NULLIF(app_count_2019, 0))::numeric,
    2
  ) AS app_count_change_2019_to_2020_pct,
  ROUND(
    (100.0 * (app_count_2021 - app_count_2020) / NULLIF(app_count_2020, 0))::numeric,
    2
  ) AS app_count_change_2020_to_2021_pct,
  ROUND(
    (100.0 * (app_count_2021 - app_count_2019) / NULLIF(app_count_2019, 0))::numeric, 
    2
  ) AS app_count_change_2019_to_2021_pct,
  ROUND(avg_wage_2019::numeric, 2) AS avg_wage_2019,
  ROUND(avg_wage_2020::numeric, 2) AS avg_wage_2020,
  ROUND(avg_wage_2021::numeric, 2) AS avg_wage_2021,
  ROUND(
    (100.0 * (avg_wage_2020 - avg_wage_2019) / NULLIF(avg_wage_2019, 0))::numeric, 
    2
  ) AS avg_wage_change_2019_to_2020_pct,
  ROUND(
    (100.0 * (avg_wage_2021 - avg_wage_2020) / NULLIF(avg_wage_2020, 0))::numeric, 
    2
  ) AS avg_wage_change_2020_to_2021_pct,
  ROUND(
    (100.0 * (avg_wage_2021 - avg_wage_2019) / NULLIF(avg_wage_2019, 0))::numeric, 
    2
  ) AS avg_wage_change_2019_to_2021_pct,
  ROUND(median_wage_2019::numeric, 2) AS median_wage_2019,
  ROUND(median_wage_2020::numeric, 2) AS median_wage_2020,
  ROUND(median_wage_2021::numeric, 2) AS median_wage_2021,
  ROUND(
    (100.0 * (median_wage_2020 - median_wage_2019) / NULLIF(median_wage_2019, 0))::numeric, 
    2
  ) AS median_wage_change_2019_to_2020_pct,
  ROUND(
    (100.0 * (median_wage_2021 - median_wage_2020) / NULLIF(median_wage_2020, 0))::numeric, 
    2
  ) AS median_wage_change_2020_to_2021_pct,
  ROUND(
    (100.0 * (median_wage_2021 - median_wage_2019) / NULLIF(median_wage_2019, 0))::numeric, 
    2
  ) AS median_wage_change_2019_to_2021_pct
FROM period_comparisons
WHERE app_count_2019 IS NOT NULL
   OR app_count_2020 IS NOT NULL
   OR app_count_2021 IS NOT NULL;

-- ============================================================================
-- INDEXES FOR FEATURE 2
-- ============================================================================

-- Index for filtering by industry
CREATE INDEX idx_covid_trend_industry 
  ON mv_covid_trend_analysis(industry);

-- Index for filtering by state
CREATE INDEX idx_covid_trend_state 
  ON mv_covid_trend_analysis(worksite_state);

-- Composite index for combined filtering
CREATE INDEX idx_covid_trend_composite 
  ON mv_covid_trend_analysis(industry, worksite_state);

-- ============================================================================
-- SUPPORTING BASE TABLE INDEXES (if not already present)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_app_fiscal_year_covid 
  ON applications(fiscal_year) 
  WHERE fiscal_year IN (2019, 2020, 2021);

CREATE INDEX IF NOT EXISTS idx_app_emp_id 
  ON applications(emp_id);

CREATE INDEX IF NOT EXISTS idx_app_site_id 
  ON applications(site_id);

-- ============================================================================
-- REFRESH COMMAND
-- ============================================================================
-- Run this after initial creation or when data updates occur:
-- REFRESH MATERIALIZED VIEW mv_covid_trend_analysis;

-- ============================================================================
-- SAMPLE QUERY USAGE
-- ============================================================================
-- Get all COVID trends:
-- SELECT * FROM mv_covid_trend_analysis;

-- Filter by specific industry:
-- SELECT * FROM mv_covid_trend_analysis WHERE industry = 'Technology';

-- Filter by specific state:
-- SELECT * FROM mv_covid_trend_analysis WHERE state = 'CA';

-- Top 10 industries with largest application drop from 2019 to 2020:
-- SELECT industry, state, app_count_change_2019_to_2020_pct
-- FROM mv_covid_trend_analysis
-- WHERE app_count_change_2019_to_2020_pct IS NOT NULL
-- ORDER BY app_count_change_2019_to_2020_pct ASC
-- LIMIT 10;
