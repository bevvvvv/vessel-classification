import os

import pandas as pd
from numpy import nanmean

from voyage_utils import voyage_finder, run_vf, assign_id, remove_dupes

files = os.listdir('./data/voyages')

for f in files:
    #######################################################################
    ######### READ DATA
    #######################################################################
    print('Reading data frame...')
    print('File name is: ' + f)
    df = pd.read_csv('./data/voyages/' + f)

    df = df.groupby(['voyage_id', 'VesselName', 'MMSI', 'VesselType']).agg({'LAT': [nanmean],
                                                                            'LON': [nanmean],
                                                                            'SOG': [nanmean],
                                                                            'Heading': [nanmean],
                                                                            'acceleration': [nanmean],
                                                                            'bearing_rate': [nanmean]}).reset_index()

    if not os.path.exists('./data/voyage_agg'):
        os.mkdir('./data/voyage_agg')
    df.to_csv('./data/voyage_agg/' + f.replace('_voyages.csv', '_voyage_agg.csv'),index=False)
