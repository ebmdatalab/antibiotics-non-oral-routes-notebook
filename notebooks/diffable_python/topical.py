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

# A user has suggested a new measure of topical preparations containing antimicrobial ([GitHub issue](https://github.com/ebmdatalab/openprescribing/issues/2481)). The [BNF states](https://bnf.nice.org.uk/drug/emollient-creams-and-ointments-antimicrobial-containing.html) that topical _Preparations containing an antibacterial should be avoided unless infection is present or is a frequent complication._
#
# In this notebook we set out to examine use of topical antibacterials.

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
        (form_route LIKE '%cream%' OR
        form_route LIKE'%oint%' OR
        form_route LIKE'%cutaneous%'
        ) 
        AND
        (bnf_code LIKE '131001%' OR # Antibacterial Preps Only Used Topically
        bnf_code LIKE '131002%' OR  #Antifungal Preparations 
        bnf_name LIKE 'Oilatum Plus%' OR #contains benzalkonium
        bnf_name LIKE 'Dermol%' OR #contains benzalkonium
        bnf_name LIKE 'Emulsiderm%') #contains benzalkonium
        )
GROUP BY pct, month, bnf_name, bnf_code
ORDER BY pct, month
'''

df_top_abx = bq.cached_read(sql, csv_path='df_top_abx.csv')
df_top_abx['month'] = df_top_abx['month'].astype('datetime64[ns]')
df_top_abx.head()

# +

df_top_abx.groupby("month")['items'].sum().plot(kind='line', title="Total items of topical antibiotics in English primary care")
plt.ylim(0, )

# +

df_top_abx.nunique()
# -

## this gives us a list of unique preparations
df_top_abx["bnf_name"].unique()

# +

##groupby bnf name + code  to see largest volume in terms of items
df_products = df_top_abx.groupby(['bnf_code', 'bnf_name']).sum().reset_index().sort_values(by = 'items', ascending = False)
df_products.head(11)
# -

# ## Map and Charts

ccg_total_abx = df_top_abx.groupby(["month", "pct"])["items"].sum().reset_index()
ccg_total_abx.head(5)

df_list = pd.read_csv('listsize.csv')
df_list['month'] = df_list['month'].astype('datetime64[ns]')
df_list.head(5)

top_abx_1000 = pd.merge(ccg_total_abx, df_list, on=['month', 'pct'])
top_abx_1000['top_abx_items_per_1000'] = 1000* (top_abx_1000['items']/top_abx_1000['list_size'])
top_abx_1000.head(5)

# +
#create sample deciles & prototype measure
charts.deciles_chart(
        top_abx_1000,
        period_column='month',
        column='top_abx_items_per_1000',
        title="Topical antibiotics items per 1000 (Bath and North East Somerset CCG) ",
        show_outer_percentiles=True)

#add in example CCG (Islington)
df_subject = top_abx_1000.loc[top_abx_1000['pct'] == '11E']
plt.plot(df_subject['month'], df_subject['top_abx_items_per_1000'], 'r--')

plt.show()
# -

#create choropeth map of items per 1000 patients
plt.figure(figsize=(12, 7))
latest_top_abx_1000 = top_abx_1000.loc[(top_abx_1000['month'] >= '2019-01-01') & (top_abx_1000['month'] <= '2019-12-01')]
plt = maps.ccg_map(latest_top_abx_1000, title="Topical antibiotics items per 1000  \n  2019 ", column='top_abx_items_per_1000', separate_london=True)
plt.show()


