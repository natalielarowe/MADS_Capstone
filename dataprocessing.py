import pandas as pd
import numpy as np
import warnings 
import geopandas as gpd
import requests, zipfile, io
from geopy import distance

## get block group coordinates
blockgroupshp = "https://www2.census.gov/geo/tiger/TIGER2023/BG/tl_2023_48_bg.zip"
r = requests.get(blockgroupshp)
zf = zipfile.ZipFile(io.BytesIO(r.content))
zf.extractall()
gdf = gpd.read_file('tl_2023_48_bg.shp')
gdf['centroid'] = gdf['geometry'].centroid
gdf['Block Group Centroid Longitude'] = gdf['centroid'].x
gdf['Block Group Centroid Latitude'] = gdf['centroid'].y
block_group_coordinates = gdf[['GEOIDFQ', 'Block Group Centroid Latitude', 'Block Group Centroid Longitude']]
block_group_coordinates = block_group_coordinates.rename(columns={'GEOIDFQ': 'Geo Index'})


def get_blockgroupshape():
    return gdf


##Decentennial DHC 2020 Rural vs Urban Population
classifurl = 'https://drive.google.com/file/d/1ViQxHHbZi7X-BkvvYBKUeDOuSvznRFVr/view?usp=share-link'
classifurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(classifurl.split('/')[-2])
classifdf = pd.read_csv(classifurl)
classifdf = classifdf[2:].reset_index(drop=True)
classifdf = classifdf.astype({'GEO_ID': 'str', 'NAME': 'str', 'P2_002N': 'int64', 'P2_003N': 'int64'})
classifdf['Classification'] = np.where(classifdf['P2_003N'] > classifdf['P2_002N'], "Rural", "Urban")
classifdf = classifdf[['GEO_ID', 'Classification']].rename(columns={'GEO_ID': 'Geo Index'})


##B25002 Occupancy of Housing Units
occurl = 'https://drive.google.com/file/d/1v4YateaDR-UTQm6XhbqLMuzv6x1ZYXmF/view?usp=share_link'
occurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(occurl.split('/')[-2])
occupancydf = pd.read_csv(occurl)
occupancydf.columns = occupancydf.iloc[0]
occupancydf = occupancydf[1:].reset_index(drop=True)
occupancydf = occupancydf[['Geography', 'Geographic Area Name', 'Estimate!!Total:!!Occupied']]
occupancydf.columns = ['Geo Index', 'Area Name', 'Occupied Housing Units']
occupancydf = occupancydf.astype({'Geo Index': 'str', 'Area Name': 'str', 'Occupied Housing Units': 'int64'})


##P1 Population Data
totalpopurl = 'https://drive.google.com/file/d/16Xwj6AaIjUAB59NhU_rq_tMiykrAwzHw/view?usp=share_link'
totalpopurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(totalpopurl.split('/')[-2])
totalpopdf = pd.read_csv(totalpopurl)
totalpopdf.columns = totalpopdf.iloc[0]
totalpopdf = totalpopdf[1:].reset_index(drop=True)
totalpopdf = totalpopdf[['Geography', ' !!Total']]
totalpopdf.columns = ['Geo Index', 'Total Population']
totalpopdf = totalpopdf.astype({'Geo Index': 'str', 'Total Population': 'int64'})


##B17017 Poverty Status (household)
povurl = 'https://drive.google.com/file/d/1Se0lYsstbDZtrOf2aSsfAzs3hSqBn_kf/view?usp=share_link'
povurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(povurl.split('/')[-2])
povdf = pd.read_csv(povurl)
povdf = povdf[['GEO_ID', 'B17017_002E']]
povdf = povdf[1:].reset_index(drop=True)
povdf.columns = ['Geo Index', 'Households Below Poverty Level']
povdf = povdf.astype({'Geo Index': 'str', 'Households Below Poverty Level': 'int64'})


##B25044 Tenure by Vehicles Available (household)
vehiclesurl = 'https://drive.google.com/file/d/1SanHZUmBEuISsFvPpr2DeVJkDG3XV3Im/view?usp=share_link'
vehiclesurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(vehiclesurl.split('/')[-2])
vehiclesdf = pd.read_csv(vehiclesurl)
vehiclesdf = vehiclesdf[['GEO_ID', 'B25044_003E', 'B25044_010E']]
vehiclesdf = vehiclesdf[1:].reset_index(drop=True)
vehiclesdf.columns = ['Geo Index', 'Owner Occupied Households No Vehicle', 'Renter Occupied Households No Vehicle']
vehiclesdf = vehiclesdf.astype({'Geo Index': 'str', 'Owner Occupied Households No Vehicle': 'int64',
                                'Renter Occupied Households No Vehicle': 'int64'})


#SNAP Retailers
snapurl = 'https://drive.google.com/file/d/1v9l5GSJdfdGWU7by6trpF6GQK9yPfAp8/view?usp=share_link'
snapurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(snapurl.split('/')[-2])
snapdf = pd.read_csv(snapurl, encoding='latin1')
snapdf = snapdf[(snapdf['State'] == 'TX')]
snapdf['Authorization Date'] = pd.to_datetime(snapdf['Authorization Date'])
snapdf = snapdf.replace("", None)
snapdf = snapdf.replace(" ", None)
snapdf['End Date'] = pd.to_datetime(snapdf['End Date'])
snapdf = snapdf[(snapdf['Authorization Date'].dt.year <= 2023) & ((snapdf['End Date'].dt.year >= 2023) | snapdf['End Date'].isnull())]
snapdf = snapdf[~snapdf['Store Name'].str.lower().str.contains('costco wholesale')]
snapdf = snapdf[~(snapdf['Store Name'].str.lower().str.contains("sam's club"))]
snapdf = snapdf[~(snapdf['Store Type'].str.lower().str.contains("military commissary"))]

snapdf_healthy = snapdf[snapdf['Store Type'].isin(['Supermarket', 'Large Grocery Store', 'Super Store'])]
snapdf_healthy = snapdf_healthy[['Record ID', 'Store Type', 'Latitude', 'Longitude']]
# ensure store coordinates are floats
snapdf_healthy['Latitude'] = snapdf_healthy['Latitude'].astype(float)
snapdf_healthy['Longitude'] = snapdf_healthy['Longitude'].astype(float)

snapdf_swamp = snapdf[snapdf['Store Type'] == 'Convenience Store']
snapdf_swamp = snapdf_swamp[['Store Type', 'Latitude', 'Longitude']]


#Fast food locations for locating food swamps
ffurl = 'https://drive.google.com/file/d/1i16keSSE16ysh0g2q_0hwgIBrzPI2zZ2/view?usp=share_link'
ffurl='https://drive.usercontent.google.com/download?id={}&export=download&authuser=0&confirm=t'.format(ffurl.split('/')[-2])
ffdf = pd.read_csv(ffurl)
ffdf = ffdf[['city', 'province', 'country', 'latitude', 'longitude']]
ffdf = ffdf[(ffdf['country'] == 'US') & (ffdf['province'] == 'TX')]
ffdf = ffdf[['latitude', 'longitude']]
ffdf = ffdf.rename(columns={'latitude': 'Latitude', 'longitude': 'Longitude'})
ffdf['Store Type'] = "Fast Food"


## Adapted from Leon's code
### Adapted from Michael Dunn in stacoverflow:
### https://stackoverflow.com/questions/4913349/haversine-formula-in-python-bearing-and-distance-between-two-gps-points
### Haversine distance function: input lat/lon ... returns km
def haversine(lon1, lat1, lon2, lat2):
    # Convert decimal degrees to radians.
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = np.sin(dlat/2.0)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2.0)**2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371 * c
    mi = km * 0.621371
    return mi

# process to find the closest store for a given tract row
def find_closest_store(row):
    lat_tract = float(row['Block Group Centroid Latitude'])
    lon_tract = float(row['Block Group Centroid Longitude'])
    # estimate vectored distances from this tract to all stores
    dists = haversine(lon_tract, lat_tract, snapdf_healthy['Longitude'].values, snapdf_healthy['Latitude'].values)
    min_idx = np.argmin(dists)
    return pd.Series({'Closest_Record_ID': snapdf_healthy.iloc[min_idx]['Record ID'],'Distance_mi': dists[min_idx],
                      'Closest store type': snapdf_healthy.iloc[min_idx]['Store Type']
    })



#Merge into one dataframe for analysis
def get_blockgroup_data():
    mergedf = pd.merge(totalpopdf, occupancydf, on='Geo Index', how='left')
    mergedf = pd.merge(mergedf, povdf, on='Geo Index', how='left')
    mergedf = pd.merge(mergedf, vehiclesdf, on='Geo Index', how='left')
    mergedf = pd.merge(mergedf, block_group_coordinates, on='Geo Index', how='left')
    mergedf = pd.merge(mergedf, classifdf, on='Geo Index', how='left')
    mergedf['Percent Poverty Level'] = mergedf['Households Below Poverty Level'] / mergedf['Occupied Housing Units']
    mergedf['Households with No Vehicle Access'] = mergedf['Owner Occupied Households No Vehicle'] + mergedf['Renter Occupied Households No Vehicle']
    mergedf = mergedf.drop(columns=['Owner Occupied Households No Vehicle', 'Renter Occupied Households No Vehicle'])
    mergedf['Percent No Vehicle Access'] = mergedf['Households with No Vehicle Access'] / mergedf['Occupied Housing Units']
    mergedf[['Closest_Record_ID', 'Distance_mi', 'Closest store type']] = mergedf.apply(find_closest_store, axis=1)
    return mergedf



"""
-ratio of unhealthy outlets (fast food, convenience stores) to healthy outlets (supermarkets/grocery stores).
-counts of fast-food and convenience stores vs. supermarkets/grocery stores within each block group (or within a set distance, like 1 mile)
-A way to distinguish outlet types (fast-food vs. full-service, convenience store vs. supermarket.)
STILL MISSING FULL SERVICE RESTAURANT LOCATIONS
"""
def get_foodswamp_data():
    foodswamp_df = pd.concat([snapdf_swamp, ffdf], ignore_index=True)
    return foodswamp_df