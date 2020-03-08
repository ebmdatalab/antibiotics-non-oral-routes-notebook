# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     notebook_metadata_filter: all,-language_info
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.3.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

#import libraries required for analysis
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from ebmdatalab import bq
from ebmdatalab import charts
from ebmdatalab import maps

# +
sql = '''
SELECT
    pct,
    CAST(month AS DATE) AS month,
    bnf_name,
    bnf_code,
    SUM(items) AS items,
    SUM(actual_cost) AS cost
FROM hscic.normalised_prescribing_standard presc
INNER JOIN hscic.practices pract ON presc.practice = pract.code
INNER JOIN
  hscic.ccgs AS ccg
ON
  presc.pct=ccg.code
WHERE
    ccg.org_type='CCG' AND
    pract.setting = 4 AND
    presc.bnf_code IN (
        SELECT DISTINCT(bnf_code)
        FROM ebmdatalab.measures.dmd_objs_with_form_route
        WHERE form_route IN ('pressurizedinhalation.inhalation', 'powderinhalation.inhalation')
        )
AND bnf_code LIKE "050%"
GROUP BY pct, month, bnf_name, bnf_code
ORDER BY pct, month
'''

df_inh_abx = bq.cached_read(sql, csv_path='df_inh_abx.csv')
df_inh_abx['month'] = df_inh_abx['month'].astype('datetime64[ns]')
df_inh_abx.head()
# -

SELECT
     CAST(month AS DATE) AS month,
     practice AS practice_id,
     SUM(items) AS denominator
 FROM hscic.normalised_prescribing_standard
 WHERE bnf_code IN (   SELECT DISTINCT(bnf_code)   FROM measures.dmd_objs_with_form_route   WHERE form_route IN ('pressurizedinhalation.inhalation', 'powderinhalation.inhalation')   AND bnf_code LIKE '03%'    AND bnf_code NOT LIKE '0301011R0%'  )
 GROUP BY month, practice_id
