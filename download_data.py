import sys
import os
import urllib.request
import zipfile

try:
    month = sys.argv[1].zfill(2)
    day = sys.argv[2].zfill(2)
except:
    print("Please enter month and day limits: python download_data.py 12 31")

# create data dir
if not os.path.exists('./data'):
    os.mkdir('./data')

days = [31] * 12
days[2]= 28
days[4] = 30
days[6] = 30
days[9] = 30
days[11] = 30
for curr_month in range(1, int(month) + 1):
    end_day = days[curr_month]
    if curr_month == int(month):
        end_day = day
    for curr_day in range(1, int(end_day) + 1):
        mo = str(curr_month).zfill(2) 
        d = str(curr_day).zfill(2)
        print('Now downloading {}/{}/2019'.format(mo, d))
        try:
            urllib.request.urlretrieve('https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2019/AIS_2019_{}_{}.zip'.format(
                mo, d), './data/AIS_{}_{}.zip'.format(mo, d))
            print('Download Successful!')
        except:
            print('Please try again later...')

should_unzip = input('Would you like to unzip the data? (y/n) >')

if should_unzip.lower() == 'y' or should_unzip.lower() == 'yes':
    for curr_month in range(1, int(month) + 1):
        for curr_day in range(1, int(day) + 1):
            mo = str(curr_month).zfill(2) 
            d = str(curr_day).zfill(2)
            path = './data/AIS_{}_{}.zip'.format(mo, d)
            print('Now unzipping {}'.format(path))
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall('./data/AIS')
            print('Succesfully unzipped {}'.format(path))
    print('Data has been successfully unzipped!')
