-- ============================================================================
-- FEATURE 3: EXPOSURE SCORE (POLICY SHOCK ANALYSIS) - FIXED v4
-- ============================================================================

DROP MATERIALIZED VIEW IF EXISTS mv_exposure_score_industry CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_exposure_score_state CASCADE;

-- ============================================================================
-- PART A: EXPOSURE SCORE BY INDUSTRY
-- ============================================================================

CREATE MATERIALIZED VIEW mv_exposure_score_industry AS
WITH base_metrics AS (
  SELECT
    e.industry,
    a.emp_id,
    COUNT(*) AS app_count_by_employer,
    SUM(COALESCE(a.annual_wage, 0)) AS wage_mass_by_employer
  FROM applications a
  JOIN employers e ON a.emp_id = e.emp_id
  WHERE a.annual_wage IS NOT NULL AND a.annual_wage > 0
  GROUP BY e.industry, a.emp_id
),
industry_totals AS (
  SELECT
    industry,
    SUM(app_count_by_employer) AS total_apps_in_industry
  FROM base_metrics
  GROUP BY industry
),
industry_aggregates AS (
  SELECT
    bm.industry,
    SUM(bm.app_count_by_employer) AS total_applications,
    SUM(bm.wage_mass_by_employer) AS total_wage_mass,
    COUNT(DISTINCT bm.emp_id) AS employer_count,
    SUM(
      POWER(
        bm.app_count_by_employer::numeric / NULLIF(it.total_apps_in_industry, 0),
        2
      )
    ) AS hhi_concentration
  FROM base_metrics bm
  JOIN industry_totals it ON bm.industry = it.industry
  GROUP BY bm.industry
),
global_totals AS (
  SELECT
    SUM(total_applications) AS global_app_count,
    SUM(total_wage_mass) AS global_wage_mass
  FROM industry_aggregates
),
scored_industries AS (
  SELECT
    ia.industry,
    ia.total_applications,
    ia.total_wage_mass,
    ia.employer_count,
    ROUND(ia.hhi_concentration::numeric, 4) AS hhi_concentration,
    ROUND(
      100.0 * ia.total_applications / NULLIF(gt.global_app_count, 0),
      2
    ) AS volume_share_pct,
    ROUND(
      100.0 * ia.total_wage_mass / NULLIF(gt.global_wage_mass, 0),
      2
    ) AS wage_mass_share_pct,
    ROUND(
      LEAST(ia.hhi_concentration::numeric, 0.25) * 100,
      2
    ) AS hhi_score
  FROM industry_aggregates ia
  CROSS JOIN global_totals gt
  WHERE ia.total_applications >= 100
)
SELECT
  si.industry,
  n.industry_name,
  si.total_applications,
  ROUND(si.total_wage_mass::numeric, 2) AS total_wage_mass,
  si.employer_count,
  si.hhi_concentration,
  si.volume_share_pct,
  si.wage_mass_share_pct,
  si.hhi_score,
  ROUND(
    (0.5 * si.volume_share_pct) + 
    (0.4 * si.wage_mass_share_pct) + 
    (0.1 * si.hhi_score),
    2
  ) AS exposure_score,
  ROUND(
    (si.total_applications * 100000)::numeric / 1000000,
    2
  ) AS estimated_fee_shock_millions
FROM scored_industries si
INNER JOIN naics_lookup n ON si.industry = n.naics_code
WHERE n.industry_name IS NOT NULL
ORDER BY exposure_score DESC;

-- ============================================================================
-- PART B: EXPOSURE SCORE BY STATE
-- ============================================================================

CREATE MATERIALIZED VIEW mv_exposure_score_state AS
WITH base_metrics AS (
  SELECT
    l.worksite_state,
    a.emp_id,
    COUNT(*) AS app_count_by_employer,
    SUM(COALESCE(a.annual_wage, 0)) AS wage_mass_by_employer
  FROM applications a
  JOIN worksite_locations l ON a.site_id = l.site_id
  WHERE a.annual_wage IS NOT NULL AND a.annual_wage > 0
  GROUP BY l.worksite_state, a.emp_id
),
state_totals AS (
  SELECT
    worksite_state,
    SUM(app_count_by_employer) AS total_apps_in_state
  FROM base_metrics
  GROUP BY worksite_state
),
state_aggregates AS (
  SELECT
    bm.worksite_state,
    SUM(bm.app_count_by_employer) AS total_applications,
    SUM(bm.wage_mass_by_employer) AS total_wage_mass,
    COUNT(DISTINCT bm.emp_id) AS employer_count,
    SUM(
      POWER(
        bm.app_count_by_employer::numeric / NULLIF(st.total_apps_in_state, 0),
        2
      )
    ) AS hhi_concentration
  FROM base_metrics bm
  JOIN state_totals st ON bm.worksite_state = st.worksite_state
  GROUP BY bm.worksite_state
),
global_totals AS (
  SELECT
    SUM(total_applications) AS global_app_count,
    SUM(total_wage_mass) AS global_wage_mass
  FROM state_aggregates
),
scored_states AS (
  SELECT
    sa.worksite_state,
    sa.total_applications,
    sa.total_wage_mass,
    sa.employer_count,
    ROUND(sa.hhi_concentration::numeric, 4) AS hhi_concentration,
    ROUND(
      100.0 * sa.total_applications / NULLIF(gt.global_app_count, 0),
      2
    ) AS volume_share_pct,
    ROUND(
      100.0 * sa.total_wage_mass / NULLIF(gt.global_wage_mass, 0),
      2
    ) AS wage_mass_share_pct,
    ROUND(
      LEAST(sa.hhi_concentration::numeric, 0.25) * 100,
      2
    ) AS hhi_score
  FROM state_aggregates sa
  CROSS JOIN global_totals gt
)
SELECT
  worksite_state,
  total_applications,
  ROUND(total_wage_mass::numeric, 2) AS total_wage_mass,
  employer_count,
  hhi_concentration,
  volume_share_pct,
  wage_mass_share_pct,
  hhi_score,
  ROUND(
    (0.5 * volume_share_pct) + 
    (0.4 * wage_mass_share_pct) + 
    (0.1 * hhi_score),
    2
  ) AS exposure_score,
  ROUND(
    (total_applications * 100000)::numeric / 1000000,
    2
  ) AS estimated_fee_shock_millions
FROM scored_states
ORDER BY exposure_score DESC;

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX idx_exposure_industry_score 
  ON mv_exposure_score_industry(exposure_score DESC);

CREATE INDEX idx_exposure_industry_name 
  ON mv_exposure_score_industry(industry);

CREATE INDEX idx_exposure_state_score 
  ON mv_exposure_score_state(exposure_score DESC);

CREATE INDEX idx_exposure_state_name 
  ON mv_exposure_score_state(worksite_state);

-- ============================================================================
-- VERIFY DATA
-- ============================================================================

SELECT 'Industry view created with ' || COUNT(*) || ' rows' AS status
FROM mv_exposure_score_industry;

SELECT 'State view created with ' || COUNT(*) || ' rows' AS status
FROM mv_exposure_score_state;

-- Show top 10 industries
SELECT industry, exposure_score, volume_share_pct, wage_mass_share_pct, hhi_score, total_applications
FROM mv_exposure_score_industry
ORDER BY exposure_score DESC
LIMIT 10;

-- Show bottom 10 industries
SELECT industry, exposure_score, volume_share_pct, wage_mass_share_pct, hhi_score, total_applications
FROM mv_exposure_score_industry
ORDER BY exposure_score ASC
LIMIT 10;

-- Show top 10 states
SELECT worksite_state, exposure_score, volume_share_pct, wage_mass_share_pct, hhi_score, total_applications
FROM mv_exposure_score_state
ORDER BY exposure_score DESC
LIMIT 10;
