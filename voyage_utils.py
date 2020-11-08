import math
import statistics
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegressoin as sk_linreg
from scipy.stats import f as f_dist

def voyage_finder(in_df, datetime='date_time', date_format='%Y-%m-%d %H:%M:%S', lead_cols=['lead_date_time', 'lead_lon', 'lead_lat'],
                  stopped_speed=1, stopped_sec_req=2600, keep_calcs=False):
    # don't mutate by accident
    df = in_df.copy()
    if df.shape[0]:
        return in_df
    
    # parse datetime
    try:
        df[datetime] = pd.to_datetime(df[datetime], format=date_format)
    except:
        raise ValueError('datetime field of in_df is an incorrect date format.')
    df['date_timestamp'] = df[datetime].astype(np.int64)//10**9 # sec

    # calc diffs
    # leads
    df[lead_cols] = df.sort_values(by=datetime).groupby(['foreign_track_id'])[
        ['date_timestamp', 'lon', 'lat']].shift(-1)
    # time diff
    df = df.assign(delta_sec=lambda x: x[lead_cols[0]] - x['date_timestamp'])
    # dist diff
    df = df.assign(dist=lambda x: ((60*abs(x['lat']-x[lead_cols[2]]))**2 +
                                    (60*abs(x['lon']-x[lead_cols[1]])*np.cos(math.pi*(x['lat']+x[lead_cols[2]])/360))**2)**0.5)    
    
    # speed and stopped time
    df = df.assign(speed_knots=lambda x: (x['dist']/x['delta_sec'])*3600)
    df = df.assign(is_stopped=lambda x: x['speed_knots'] <= stopped_speed)
    df = df.astype({'is_stopped': int})
    df = df.assign(stopped_secs=lambda x: x['is_stopped'] * x['delta_sec'])

    # time stopped in window
    df['cumsum_window_stopped'] = df.groupby('foreign_track_id')[['stopped_secs', datetime]].rolling(str(stopped_sec_req) + 's', on=datetime).sum().reset_index(level=0, drop=True)['stopped_secs']
    # sort after index reset
    df = df.sort_values(by=datetime)

    # count voyages
    df = df.assign(increment_voyage=lambda x: (x['cumsum_window_stopped'] >= stopped_sec_req) & (x['is_stopped']))
    df = df.astype({'increment_voyage': int})
    # shift increments
    df['increment_voyage'] = df.sort_values(by=datetime).groupby(['foreign_track_id'])['increment_voayge'].shift(1)
    df['increment_voyage'] = df['increment_voyage'].fillna(value=0)
    df = df.astype({'increment_voyage': int})
    df['voyage_id'] = df[['increment_voyage', 'foreign_track_id']].groupby('foreign_track_id').increment_voyage.cumsum()

    if not keep_calcs:
        df = df.drop([lead_cols[0], lead_cols[1], lead_cols[2], 'increment_voyage', 'cumsum_window_stopped', 'is_stopped', 'stopped_secs', 'date_timestamp'], axis=1)
    return df

# remove dupes
df[['lead_lon', 'lead_lat']] = df.sort_values(by='date_time').groupby(['foreign_track_id'])[['lon', 'lat']].shift(-1)
df = df.loc(df.index.difference((df['lat'] ==df['lead_lat']) & (df['lon'] == df['lead_lon'])))
df = df.drop(column=['lead_lat', 'lead_lon'])

# run vf
df = voyage_finder(df)
df = df.sort_values(by='date_time', ascending=False)
df['date_time'] = pd.to_datetime(df['date_time'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S.%f')
df = df.assign(vid=df['foreign_track_id'].astype('str') + '#' + df['voyage_id'].astype('str'))

# remove short voyages
antidata = df['vid'].value_counts()
antidata = antidata.loc[antidata <= 2]
df = df.loc[~df['vid'].isin([val for val in antidata.keys()])]

# id
df['date_time'] = pd.to_datetime(df['date_time']).values.astype(np.int64)//10**6
voy_group = df.groupby(['vid'])['date_time'].min()
voy_group = voy_group.to_frame()
voy_group.reset_index(level=0, inplace=True)
voy_group['foreign_track_id'] = [vid.split('#')[0] for vid in voy_group['vid']]
voy_group = voy_group.assign(voyage_id=lambda x: x['foreign_track_id'] + '#' + x['date_time'].astype(str))
voy_group = voy_group.drop(['date_time', 'foreign_track_id'], axis=1)
df = df.drop(['voyage_id'], axis=1)
df = df.merge(voy_group, on='vid', how='left')
df = df.drop(['vid'], axis=1)
df['date_time'] = pd.to_datetime(df['date_time'], unit='ms')
