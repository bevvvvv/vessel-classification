# vessel-classification

DS340W Project identifying maritime vessels based off kinematic information.

Please reference [noaa.gov](https://coast.noaa.gov/htdata/CMSP/AISDataHandler/2019/index.html) for historical datasets.

## Downloading Data

To download data please make use of the download_data.py script to download data direction from NOAA. Currently the script will download starting from January 1, 2019. The following command will download data between January 1, 2019 and February 28, 2019. Note that the full year is 99GB.

`python download_data.py 2 28`
