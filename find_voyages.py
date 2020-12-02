import os

import pandas as pd

from voyage_utils import voyage_finder, run_vf, assign_id, remove_dupes, calc_accel, calc_bearing_rate

files = os.listdir('./data/AIS')

for f in files:
    #######################################################################
    ######### READ DATA
    #######################################################################

    print('Reading data frame...')
    print('File name is: ' + f)
    df = pd.read_csv('./data/AIS/' + f)
    num_points = df.shape[0]
    num_ships = len(df.MMSI.unique())

    #######################################################################
    ######### CONVERT DATE TO EPOCH
    #######################################################################

    print('Converting date timestamp...')
    df['BaseDateTime'] = pd.to_datetime(df['BaseDateTime'].astype(str))#, format="%Y-%m-%dT%H:%M:S")

    #######################################################################
    ######### RUN VF METHODS
    #######################################################################

    print('Running voyage_finder...')
    #df = remove_dupes(df)
    df = run_vf(df)
    df = assign_id(df)
    df = calc_accel(df)
    df = calc_bearing_rate(df)
    print('Found voyages!')

    #######################################################################
    ######### WRITE TO NEW FILE
    #######################################################################

    if not os.path.exists('./data/voyages'):
        os.mkdir('./data/voyages')
    df.to_csv('./data/voyages/' + f.replace('.csv', '_voyages.csv'))

    print('Point difference: ', df.shape[0] - num_points)
    print('Ship difference: ', len(df.MMSI.unique()) - num_ships)
    print('Voyages found: ', len(df.voyage_id.unique()))
