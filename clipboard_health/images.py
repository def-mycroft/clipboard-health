import plotly.express as px
from os.path import split, join
import pandas as pd
from clipboard_health.main import ROLETYPE_NAMES
from clipboard_health import main as ch

COLORS = ['#1F7ABE', '#F0C277', '#C48646', '#D80A0C', '#000000', '#0E1B35',
          '#635D70', '#463F1A']


def build_images(base_data, dev_path=True):
    tch_crr_by_state(base_data, dev_path=dev_path)
    deficit_hours_by_state(base_data, dev_path=dev_path)
    plot_prob_shortfall_day(base_data, dev_path=dev_path)

    hours_by_role(base_data, dev_path=dev_path)
    hours_by_state(base_data, dev_path=dev_path)


def plot_prob_shortfall_day(base_data, dev_path=True):
    d = prep_prob_shortfall_day(base_data)
    fig = px.scatter(
        d,
        x='n_shortfall_days',
        y='prob_shortfall_day',
        labels={'n_shortfall_days': 'Number of Facility-Days in Deficit', 
                'prob_shortfall_day': 'Percent of Shortfall Days'},
        trendline='ols',
        title='Staffing Shortfall Facility-Days',
        text='statelab', 
        custom_data=['hover_text'],
    )

    fig.update_traces(
        marker=dict(color=COLORS[0]),
        hovertemplate='%{customdata[0]}',
        textposition='top center'
    )

    fig.data[1].line.color = COLORS[1]

    write_image(fig, 'prob-shortfall-day', dev_path=dev_path)

    return fig


def prep_prob_shortfall_day(base_data):
    df = calc_deficit(base_data)
    base_data['is_shortfall_day'] = (base_data['staffing_shortfall_score'] > 0).astype(int)
    d = pd.concat([
        df.groupby('state').count()['date'],
        df.groupby('state')['is_shortfall_day'].sum(),
    ], axis=1).rename(columns={'date':'n_days', 'is_shortfall_day':'n_shortfall_days'})
    d['prob_shortfall_day'] = d['n_shortfall_days'] / d['n_days']
    d = d.reset_index()

    states_label = ['tx']
    d['hover_text'] = d.apply(
        lambda row: f"State: {row['state']}<br>"
                    f"Percent Shortfall Days: {100*row['prob_shortfall_day']:.1f}%<br>"
                    f"Number of Facility-Days in Deficit: {row['n_shortfall_days']:,.1f}<br>",
                    axis=1
    )
    states_label = ['tx', 'mo', 'in', 'ok', 'nm', 'il', 'oh', 'ga', 'wy',
                    'ks', 'ne', 'sd', 'ca', 'pa', 'fl', 'nc', 'wa']
    states_label = [x.upper() for x in states_label]

    d['statelab'] = d['state']
    d.loc[~d['state'].isin(states_label), 'statelab'] = ''


    return d


def deficit_hours_by_state(base_data, dev_path=True):
    """Hours Deficit by State"""
    hours = prep_deficit_hours_by_state(base_data)
    fig = px.scatter(
        hours,
        x='staffing_shortfall_resident_hours',
        y='staffing_shortfall_score',
        labels={'staffing_shortfall_resident_hours': 'Aggregate Hours Deficit', 
                'staffing_shortfall_score': 'Deficit Score'},
        custom_data=['hover_text'],
        trendline='ols',
        text='statelab',
        title='Staffing Shortfall Hours',
    )
    fig.update_traces(
        marker=dict(color=COLORS[0]),
        hovertemplate='%{customdata[0]}',
        textposition='top center'
    )
    fig.data[1].line.color = COLORS[1]

    write_image(fig, 'deficit-by-state', dev_path=dev_path)

    return fig


def prep_deficit_hours_by_state(base_data):
    s = base_data.groupby('state')[ch.HOURS_COLS + ['mdscensus']].sum()
    s = calc_deficit(s).reset_index()
    s['staffing_shortfall_resident_hours'] = s['staffing_shortfall_score'] * s['mdscensus']

    s['hover_text'] = s.apply(
        lambda row: f"State: {row['state']}<br>"
                    f"Staffing Shortfall Hours: {row['staffing_shortfall_resident_hours']:.0f}<br>"
                    f"Staffing Shortfall Score: {row['staffing_shortfall_score']:.3f}<br>",
                    axis=1
    )
    states_label = ['tx', 'mo', 'in', 'ok', 'nm', 'il', 'oh', 'ga', 'wy',
                    'ny', 'ks', 'ne', 'va', 'sd']
    states_label = [x.upper() for x in states_label]

    s['statelab'] = s['state']
    s.loc[~s['state'].isin(states_label), 'statelab'] = ''


    return s


def calc_deficit(df):
    df['hprd_rn'] = df['hrs_rn'] / df['mdscensus']  
    df['hprd_cna'] = df['hrs_cna'] / df['mdscensus']  
    df['hprd_lpn'] = df['hrs_lpn'] / df['mdscensus']  
    df['hprd_total'] = (df['hrs_rn'] + df['hrs_cna'] + df['hrs_lpn']) / df['mdscensus']  

    df['hprd_rn_deficit'] = (0.55 - df['hprd_rn']).clip(lower=0)  
    df['hprd_cna_deficit'] = (2.45 - df['hprd_cna']).clip(lower=0)  
    df['hprd_total_deficit'] = (3.48 - df['hprd_total']).clip(lower=0)  

    df['staffing_shortfall_score'] = df['hprd_total_deficit'] / 3.48

    return df


def prep_tch_crr_state_data(base_data, states_label=[]):
    d = prep_hours_by_state(base_data, ctr_hours=True)
    hours_contractor = d.set_index('state').sum(axis=1).rename('hours_ctr')
    d = prep_hours_by_state(base_data, ctr_hours=False)
    hours_total = d.set_index('state').sum(axis=1).rename('hours_total')
    hours = pd.concat([hours_contractor, hours_total], axis=1).reset_index()
    hours['pct_ctr'] = hours['hours_ctr'] / hours['hours_total']
    hours['hover_text'] = hours.apply(
        lambda row: f"State: {row['state']}<br>"
                    f"Total Contractor Hours: {row['hours_ctr']/1000:,.0f}K<br>"
                    f"CRR: {row['pct_ctr']:.2%}", axis=1
    )
    hours['statelab'] = hours['state']
    hours.loc[~hours['state'].isin(states_label), 'statelab'] = ''

    return hours


def tch_crr_by_state(base_data, dev_path=True):
    """Total Contractor Hours and Ctr Reliance by State"""
    states_label = ['NY', 'PA', 'NJ', 'VT', 'ME', 'MT', 'AK', 'CA', 'MD', 'TX',
                    'FL']
    hours = prep_tch_crr_state_data(base_data, states_label=states_label)
    fig = px.scatter(
        hours,
        x='hours_ctr',
        y='pct_ctr',
        labels={'hours_ctr': 'Total Contractor Hours', 
                'pct_ctr': 'Contractor Reliance Rate (%)'},
        custom_data=['hover_text'],
        text='statelab',
        trendline='ols',
        title='Total Contractor Hours and Contractor Reliance Rate by State',
    )
    fig.update_traces(
        marker=dict(color=COLORS[0]),
        hovertemplate='%{customdata[0]}',
        textposition='top center'
    )
    fig.data[1].line.color = COLORS[1]

    write_image(fig, 'tch-crr', dev_path=dev_path)

    return fig


def group_ratio_hours(base_data, roletype):
    """Group hours by employee vs contractor for given roletype"""
    cols = [
        roletype,
        f"{roletype}_emp",
        f"{roletype}_ctr",
    ]
    x = base_data[cols].sum().to_dict()
    d = {}
    d['roletype'] = cols[0]
    d['hours_total'] = x[cols[0]]
    d['hours_emp'] = x[cols[1]]
    d['hours_ctr'] = x[cols[2]]

    return d


def prep_ctr_ratio_hours(base_data, fancy=False):
    data = []

    for col in ch.HOURS_COLS:
        data.append(group_ratio_hours(base_data, col))
    d = pd.DataFrame(data).set_index('roletype') / 1000
    d['ctr_ratio'] = d['hours_ctr'] / d['hours_total']
    d = d.sort_values(by=['hours_total'], ascending=False)
    d['market_share_pareto'] = d['hours_ctr'] / d['hours_ctr'].sum()

    if fancy:
        for col in ['hours_total', 'hours_emp', 'hours_ctr']:
            d[col] = d[col].apply(lambda x: f"{x:,.0f}K")

        for col in ['ctr_ratio', 'market_share_pareto']:
            d[col] = d[col].apply(lambda x: f"{100*x:.1f}%")
        colmap = {'hours_total':'Total Hours', 'hours_emp':'Employee Hours', 
                  'hours_ctr':'Contractor Hours', 
                  'ctr_ratio':'Contractor / Total', 
                  'market_share_pareto':'Contractor Market Share',
                  }
        d = d.rename(columns=colmap)
        d.index = d.index.map(ROLETYPE_NAMES)

    return d


def write_image(fig, filename, dev_path=False, width=700):
    dir_out = paths(dev_path=dev_path)
    fp = join(dir_out, f"{filename}.html")
    fig.write_html(fp)
    height = width / 1.618
    fig.write_image(fp.replace('.html', '.png'), width=width, height=height)
    print(f"wrote '{fp}'")


def paths(dev_path=False):
    if not dev_path:
        dir_out = join(split(split(__file__)[0])[0], 'images')
    else:
        dir_out = '/l/tmp'

    return dir_out


def hours_by_role(base_data, dev_path=True):
    colmap = {'index':'Role Type', 'value':'Percentage of All Hours'}
    roles = base_data[ch.HOURS_COLS].sum()
    roles = roles / roles.sum()
    roles = roles.sort_values(ascending=False)
    roles = roles.rename('role')
    roles = (pd.DataFrame(roles).reset_index()
               .melt(id_vars='index', value_vars='role')
               .drop(columns=['variable']).rename(columns=colmap))
    roles[colmap['index']] = roles[colmap['index']].map(ROLETYPE_NAMES)
    roles[colmap['value']] *= 100

    colors = dict(zip(roles[colmap['index']].values, COLORS[:len(roles)]))

    fig = px.bar(roles, x=colmap['index'], y=colmap['value'],
                 color_discrete_map=colors, color=colmap['index'])
 
    write_image(fig, 'hours-by-role', dev_path=dev_path)

    return fig 


def prep_hours_by_state(base_data, ctr_hours=True):
    """Setup data for hours by state"""
    if ctr_hours:
        cols = ch.HOURS_COLS_CTR
    else:
        cols = ch.HOURS_COLS
    gr = base_data.groupby('state')[cols].sum()
    if ctr_hours:
        gr.columns = [x.replace('_ctr', '') for x in gr.columns]
    idx = gr.sum(axis=1).sort_values().index.tolist()
    gr = gr.reindex(idx)
    gr = gr.reset_index()

    return gr


def hours_by_state(base_data, dev_path=True):
    """Horizontal barplot of hours by state"""

    df = prep_hours_by_state(base_data.copy())

    roletype_order = [
        'hrs_cna', 
        'hrs_lpn', 
        'hrs_rn', 
        'hrs_medaide',
        'hrs_rnadmin', 
        'hrs_lpnadmin', 
        'hrs_rndon', 
        'hrs_natrn', 
    ]

    color_map = dict(zip(roletype_order, COLORS[:len(roletype_order)]))
    color_map = {ROLETYPE_NAMES[k]:v for k,v in color_map.items()}

    df_melted = df.melt(id_vars=['state'], value_vars=roletype_order,
                        var_name='category', value_name='hours')
    df_melted['category'] = df_melted['category'].map(ROLETYPE_NAMES)

    fig = px.bar(df_melted, 
                 y='state', 
                 x='hours', 
                 color='category',
                 orientation='h',
                 color_discrete_map=color_map)

    write_image(fig, 'hours-by-state', dev_path=dev_path)

    return fig
