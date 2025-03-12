import pandas as pd

BASE_COLS = ['provnum', 'city', 'state', 'county_name', 'county_fips', 'cy_qtr',
             'workdate']
FP_BASE_DATA = '/d/PBJ_Daily_Nurse_Staffing_Q2_2024.csv'
ROLETYPE_NAMES = {
    'hrs_rndon': 'RN Director of Nursing',
    'hrs_rnadmin': 'RN with Admin Duties',
    'hrs_rn': 'Registered Nurse',
    'hrs_lpnadmin': 'LPN with Admin Duties',
    'hrs_lpn': 'Licensed Practical Nurse',
    'hrs_cna': 'Certified Nursing Assistant',
    'hrs_natrn': 'Nurse Aide Trainee',
    'hrs_medaide': 'Medication Aide'
}

HOURS_COLS = ['hrs_rndon', 'hrs_rnadmin', 'hrs_rn', 'hrs_lpnadmin', 'hrs_lpn',
              'hrs_cna', 'hrs_natrn', 'hrs_medaide']
HOURS_COLS_CTR = [f"{x}_ctr" for x in HOURS_COLS]


def load_base_data():
    df = pd.read_csv(FP_BASE_DATA,
                     encoding='latin1', low_memory=False)
    df.columns = [x.lower() for x in df.columns]
    assert df[BASE_COLS].drop_duplicates().shape[0] / len(df) == 1

    df.columns = [x.lower() for x in df.columns]
    df['date'] = df['workdate']

    return df

