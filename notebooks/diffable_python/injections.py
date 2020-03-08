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

# https://github.com/ebmdatalab/openprescribing/issues/2384

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
        WHERE 
        (form_route LIKE '%intravenous%' OR
        form_route LIKE'%injection%' OR
        form_route LIKE'%subcutaneous')      
        AND bnf_code LIKE "050%")
GROUP BY pct, month, bnf_name, bnf_code
ORDER BY pct, month
'''

df_inj_abx = bq.cached_read(sql, csv_path='df_inj_abx.csv')
df_inj_abx['month'] = df_inj_abx['month'].astype('datetime64[ns]')
df_inj_abx.head()
# -

df_inj_abx.groupby("month")['items'].sum().plot(kind='line', title="Total items of injectable antibiotics in English primary care")
plt.ylim(0, )

df_inj_abx.nunique()

df_inj_abx["bnf_name"].unique()

##groupby bnf name  to see largest volume in terms of items
df_products = df_inj_abx.groupby(['bnf_code', 'bnf_name']).sum().sort_values(by = 'items', ascending = False).reset_index()
df_products.head(26)

sql2 = """
SELECT
  month,
  pct_id AS pct,
  SUM(total_list_size) AS list_size
FROM
  ebmdatalab.hscic.practice_statistics
GROUP BY
  month,
  pct
ORDER BY
  month,
  pct,
  list_size
"""
df_list = bq.cached_read(sql2, csv_path='listsize.csv')
df_list['month'] = df_list['month'].astype('datetime64[ns]')
df_list.head(5)

ccg_total_abx = df_inj_abx.groupby(["month", "pct"])["items"].sum().reset_index()
ccg_total_abx.head(5)

df_abx_1000 = pd.merge(ccg_total_abx, df_list, on=['month', 'pct'])
df_abx_1000['inj_abx_items_per_1000'] = 1000* (df_abx_1000['items']/df_abx_1000['list_size'])
df_abx_1000.head(5)

# +
#create sample deciles & prototype measure
charts.deciles_chart(
        df_abx_1000,
        period_column='month',
        column='inj_abx_items_per_1000',
        title="Injectable antibiotics items per 1000 (Islington CCG) ",
        show_outer_percentiles=False)

#add in example CCG (Islington)
df_subject = df_abx_1000.loc[df_abx_1000['pct'] == '08H']
plt.plot(df_subject['month'], df_subject['inj_abx_items_per_1000'], 'r--')

plt.show()
# -

#create choropeth map of cost per 1000 patients
plt.figure(figsize=(12, 7))
latest_df_abx_1000 = df_abx_1000.loc[(df_abx_1000['month'] >= '2019-01-01') & (df_abx_1000['month'] <= '2019-12-01')]
plt = maps.ccg_map(latest_df_abx_1000, title="Injectable antibiotics items per 1000  \n  2019 ", column='inj_abx_items_per_1000', separate_london=True)
plt.show()


