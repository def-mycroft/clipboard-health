
from zero_helpers.imports import * 
from clipboard_health import images as chi
from clipboard_health import main as ch

COLS_ROUND = [
    'tch',
    'tch_norm',
    'def_hours',
    'def_hours_norm',
    'prob_sday',
    'prob_sday_norm',
    'n_def_days',
    'n_def_days_norm',
    'mean_residents',
    'mean_residents_norm',
    'crr',
    'crr_norm',
    'th',
    'th_norm',
]


COL_ORDER = [
    'provnum',
    'tch',
    'tch_norm',
    'def_hours',
    'def_hours_norm',
    'prob_sday',
    'prob_sday_norm',
    'n_def_days',
    'n_def_days_norm',
    'mean_residents',
    'mean_residents_norm',
    'crr',
    'crr_norm',
    'th',
    'th_norm',
    'provname',
    'city',
    'county_name',
    'county_fips',
    'state',
]


COLMAP = {
    'provnum':'Provider Number',
    'tch':'Total Contractor Hours (TCH)',
    'tch_norm':'TCH Score',
    'def_hours':'Deficit Hours',
    'def_hours_norm':'Deficit Hours Score',
    'prob_sday':'Percent of Day in Deficit',
    'prob_sday_norm':'Percent of Day in Deficit Score',
    'n_def_days':'Count Deficit Days',
    'n_def_days_norm':'Count Deficit Days Score',
    'mean_residents':'Average Residents per Day',
    'mean_residents_norm':'Average Residents per Day Score',
    'crr':'Contractor Reliance Rate (CRR)',
    'crr_norm':'CRR Score',
    'th':'Total Hours',
    'th_norm':'Total Hours Score',
    'provname':'Provider Name',
    'city':'City',
    'county_name':'County',
    'county_fips':'County Number',
    'state':'State',
}


def make_it_pretty(d):
    for col in COLS_ROUND:
        d[col] = d[col].apply(lambda x: f"{x:.1f}")
    d = d.reset_index()[COL_ORDER].rename(columns=COLMAP)
    return d


def setup_aggregate_data(base_data, make_pretty=True):
    base_data = chi.calc_deficit(base_data)
    base_data['is_shortfall_day'] = (base_data['staffing_shortfall_score'] > 0).astype(int)

    data = {
        'tch':base_data.groupby('provnum')[ch.HOURS_COLS_CTR].sum().sum(axis=1),
        'th':base_data.groupby('provnum')[ch.HOURS_COLS].sum().sum(axis=1),
        'def_hours':base_data.groupby('provnum')['hprd_total_deficit'].sum(),
        'n_days':base_data.groupby('provnum').count()['date'],
        'n_def_days':base_data.groupby('provnum')['is_shortfall_day'].sum(),
        'mean_residents':base_data.groupby('provnum')['mdscensus'].mean(),
    }
    d = pd.DataFrame(data)
    d['prob_sday'] = d['n_def_days'] / d['n_days']
    d['crr'] = d['tch'] / d['th']

    cols = ['provname', 'city', 'county_name', 'county_fips', 'state']
    s = (base_data.drop_duplicates(subset=['provnum']).set_index('provnum')[cols]
           .sort_values(by=['provname']))
    d = d.join(s)

    # calculate z-score for every key metric by state 
    order_cols = []
    cols = ['tch', 'def_hours', 'prob_sday', 'n_def_days',
            'mean_residents', 'crr', 'th']
    for state in d['state'].unique():
        for col in cols:
            m = d['state'] == state
            d.loc[m, f"{col}_norm"] = (d.loc[m, col] - d.loc[m, col].mean()) / \
                d.loc[m, col].mean()
            if col not in order_cols:
                order_cols.extend([col, f"{col}_norm"])

    cols = order_cols + [x for x in d.columns if x not in order_cols]
    inv_cols = ['def_hours', 'n_def_days', 'crr', 'tch', 'th']
    for col in inv_cols:
        d[col] = d[col] * -1

    d = (d[cols].sort_values(by=['def_hours', 'n_def_days', 'tch', 'crr'])
          .reset_index(drop=False).reset_index())
    d.index = d.index.rename('sort_index')

    # invert cols back
    for col in inv_cols:
        d[col] = d[col] * -1
    if make_pretty:
        d = make_it_pretty(d)

    return d
