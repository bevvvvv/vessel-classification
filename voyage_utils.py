import math
import statistics
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression as sk_linreg
from scipy.stats import f as f_dist

def voyage_finder(in_df, datetime='BaseDateTime', date_format='%Y-%m-%d %H:%M:%S', lead_cols=['lead_date_time', 'lead_LON', 'lead_LAT'],
                  stopped_speed=1, stopped_sec_req=2600, keep_calcs=False):
    # don't mutate by accident
    df = in_df.copy()
    if df.shape[0] <= 1:
        return in_df
    
    # parse datetime
    try:
        df[datetime] = pd.to_datetime(df[datetime], format=date_format)
    except:
        raise ValueError('datetime field of in_df is an incorrect date format.')
    df['date_timestamp'] = df[datetime].astype(np.int64)//10**9 # sec

    # calc diffs
    # leads
    df[lead_cols] = df.sort_values(by=datetime).groupby(['MMSI'])[
        ['date_timestamp', 'LON', 'LAT']].shift(-1)
    # time diff
    df = df.assign(delta_sec=lambda x: x[lead_cols[0]] - x['date_timestamp'])
    # dist diff
    df = df.assign(dist=lambda x: ((60*abs(x['LAT']-x[lead_cols[2]]))**2 +
                                    (60*abs(x['LON']-x[lead_cols[1]])*np.cos(math.pi*(x['LAT']+x[lead_cols[2]])/360))**2)**0.5)    
    
    # speed and stopped time
    df = df.assign(speed_knots=lambda x: (x['dist']/x['delta_sec'])*3600)
    df = df.assign(is_stopped=lambda x: x['speed_knots'] <= stopped_speed)
    df = df.astype({'is_stopped': int})
    df = df.assign(stopped_secs=lambda x: x['is_stopped'] * x['delta_sec'])

    # time stopped in window
    df['cumsum_window_stopped'] = df.groupby('MMSI')[['stopped_secs', datetime]].rolling(str(stopped_sec_req) + 's', on=datetime).sum().reset_index(level=0, drop=True)['stopped_secs']
    # sort after index reset
    df = df.sort_values(by=datetime)

    # count voyages
    df = df.assign(increment_voyage=lambda x: (x['cumsum_window_stopped'] >= stopped_sec_req) & (x['is_stopped']))
    df = df.astype({'increment_voyage': int})
    # shift increments
    df['increment_voyage'] = df.sort_values(by=datetime).groupby(['MMSI'])['increment_voyage'].shift(1)
    df['increment_voyage'] = df['increment_voyage'].fillna(value=0)
    df = df.astype({'increment_voyage': int})
    df['voyage_id'] = df[['increment_voyage', 'MMSI']].groupby('MMSI').increment_voyage.cumsum()

    if not keep_calcs:
        df = df.drop([lead_cols[0], lead_cols[1], lead_cols[2], 'increment_voyage', 'cumsum_window_stopped', 'is_stopped', 'stopped_secs', 'date_timestamp'], axis=1)
    return df

def remove_dupes(df):
    # remove dupes
    df[['lead_LON', 'lead_LAT']] = df.sort_values(by='BaseDateTime').groupby(['MMSI'])[['LON', 'LAT']].shift(-1)
    df = df.iloc(df.index.difference((df['LAT'] ==df['lead_LAT']) & (df['LON'] == df['lead_LON'])))
    df = df.drop(column=['lead_LA', 'lead_LON'])
    return df

def run_vf(df):
    # run vf
    df = voyage_finder(df)
    df = df.sort_values(by='BaseDateTime', ascending=False)
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S.%f')
    df = df.assign(vid=df['MMSI'].astype('str') + '#' + df['voyage_id'].astype('str'))
    return df

def assign_id(df):
    # remove short voyages
    antidata = df['vid'].value_counts()
    antidata = antidata.loc[antidata <= 2]
    df = df.loc[~df['vid'].isin([val for val in antidata.keys()])]

    # id
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime']).values.astype(np.int64)//10**6
    voy_group = df.groupby(['vid'])['BaseDateTime'].min()
    voy_group = voy_group.to_frame()
    voy_group.reset_index(level=0, inplace=True)
    voy_group['MMSI'] = [vid.split('#')[0] for vid in voy_group['vid']]
    voy_group = voy_group.assign(voyage_id=lambda x: x['MMSI'] + '#' + x['BaseDateTime'].astype(str))
    voy_group = voy_group.drop(['BaseDateTime', 'MMSI'], axis=1)
    df = df.drop(['voyage_id'], axis=1)
    df = df.merge(voy_group, on='vid', how='left')
    df = df.drop(['vid'], axis=1)
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'], unit='ms')

    return df

def calc_accel(df, speed_col='SOG'):
    df[speed_col] = df[speed_col].fillna(0)
    # diff over 2
    df[['lead_speed']] = df.sort_values(by='BaseDateTime').groupby(['MMSI'])[[speed_col]].shift(-1)
    df['acceleration'] = (df['lead_speed'] - df[speed_col]) / df['delta_sec']
    df = df.drop(['lead_speed'],axis=1)
    return df

def calc_bearing_rate(df, bearing_col='Heading'):
    df[bearing_col] = df[bearing_col].fillna(0)
    # diff over 2
    df[['lead_bearing']] = df.sort_values(by='BaseDateTime').groupby(['MMSI'])[[bearing_col]].shift(-1)
    df['bearing_rate'] = (df['lead_bearing'] - df[bearing_col]) / df['delta_sec']
    df = df.drop(['lead_bearing'],axis=1)
    return df
