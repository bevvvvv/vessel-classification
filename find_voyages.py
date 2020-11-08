import pandas as pd

from voyage_utils import voyage_finder, run_vf, assign_id, remove_dupes

#######################################################################
######### READ DATA
#######################################################################

print('Reading data frame...')
df = pd.read_csv('./data/AIS/AIS_2019_01_01.csv')
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
print('Found voyages!')

#######################################################################
######### WRITE TO NEW FILE
#######################################################################

df.to_csv('./data/AIS_voyage_01_01.csv')

print('Point difference: ', df.shape[0] - num_points)
print('Ship difference: ', len(df.MMSI.unique()) - num_ships)
print('Voyages found: ', len(df.voyage_id.unique()))
