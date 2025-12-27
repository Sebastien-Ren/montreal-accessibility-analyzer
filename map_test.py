import pandas as pd
import numpy as np
import folium
import osmnx
import geopandas
import matplotlib
from shapely import Point
from folium.plugins import HeatMap

m = folium.Map(location=(45.5019, -73.5674), control_scale=True, zoom_start=15)

mtl_boundaries = osmnx.geocoder.geocode_to_gdf("Montreal", which_result=None)
boundary = folium.FeatureGroup(name="boundary")

min_lon = mtl_boundaries.bounds.minx
max_lon = mtl_boundaries.bounds.maxx
min_lat = mtl_boundaries.bounds.miny
max_lat = mtl_boundaries.bounds.maxy

#get mtl's bounding box and create evenly spaced coord arrays
lon_values = np.linspace(min_lon, max_lon, 50)
lat_values = np.linspace(min_lat, max_lat, 50)

#combine lat and lon arrays into list of coordinate pairs (lon, lat)
coord_pairs = np.array(np.meshgrid(lon_values, lat_values)).T.reshape(-1,2)
list_points = [Point(lon, lat) for lon, lat in coord_pairs]

gdf = geopandas.GeoDataFrame(crs="EPSG:4326", geometry=list_points)
#print(gdf.head())

print(f"# of points before: {len(list_points)}")

#filtered points to only allow points within polygon boundary of mtl
pts_in_boundary = gdf.sjoin(mtl_boundaries, how="inner")

#print(pts_in_boundary.head())

points_layer = folium.FeatureGroup(name="grid points", show=False)

#adding grid points to folium map to visualize, icon color as green
for row in pts_in_boundary.itertuples():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5,
        color="green",
        fill=True,
        fillColor="green",
        fillOpacity=0.6
    ).add_to(points_layer)

points_layer.add_to(m)

folium.GeoJson(mtl_boundaries).add_to(boundary)

mtl_pts_of_interest = osmnx.features.features_from_place("Montreal", {'shop': ['supermarket','grocery']}, which_result=None)

#filter for only points, no polygons for now
mtl_pts_of_interest = mtl_pts_of_interest[mtl_pts_of_interest.geometry.type == 'Point']
grocery_stores = folium.FeatureGroup(name="grocery stores")

#iterate through grocery stores
for index, row in mtl_pts_of_interest.iterrows():
    y = row.geometry.y
    x = row.geometry.x

    popup_text = ""

    if not pd.isna(row['name']):
        popup_text += f"Name: {row['name']}\n"

    if not pd.isna(row['shop']):
        popup_text += f"Type: {row['shop']}\n"

    if not pd.isna(row['brand']):
        popup_text += f"Brand: {row['brand']}\n"

    if not pd.isna(row['opening_hours']):
        popup_text += f"Hours: {row['opening_hours']}\n"

    folium.Marker(location=[y, x], popup=popup_text).add_to(grocery_stores)

grocery_stores.add_to(m)
boundary.add_to(m)

#print(f"Found {len(mtl_pts_of_interest)} stores")

#print(mtl_pts_of_interest.head())
#print(mtl_pts_of_interest.columns)

#reproject all points from (lat/lon degrees) to a metric CRS
pts_in_boundary = pts_in_boundary.to_crs(3857)
mtl_pts_of_interest = mtl_pts_of_interest.to_crs(3857)

#calculating distances of each grid point to ALL grocery stores
distances_list = []
for point in pts_in_boundary.geometry:
    temp_distances = []
    for grocery in mtl_pts_of_interest.geometry:
        temp_distances.append(point.distance(grocery))
    
    distances_list.append(min(temp_distances))

pts_in_boundary['nearest_distance'] = distances_list

# Basic stats
print(f"Minimum distance: {pts_in_boundary['nearest_distance'].min()} meters")
print(f"Maximum distance: {pts_in_boundary['nearest_distance'].max()} meters")
print(f"Average distance: {pts_in_boundary['nearest_distance'].mean()} meters")
print(f"Median distance: {pts_in_boundary['nearest_distance'].median()} meters \n")

#scoring function
def scoring_distance(distance):
    if(distance >= 0 and distance < 500):
        return 5
    elif(distance >= 500 and distance < 1000):
        return 4
    elif(distance >= 1000 and distance < 2000):
        return 3
    elif(distance >= 2000 and distance < 3000):
        return 2
    elif(distance >= 3000):
        return 1

#apply scoring function to distances in dataframe
pts_in_boundary['accessibility_score'] = pts_in_boundary['nearest_distance'].apply(scoring_distance)

#STATISTICS
print("KEY FINDINGS:")

# How many pts in each score category?
count = pts_in_boundary['accessibility_score'].value_counts()
print(f"# of pts in each score category: \n {count} \n")

# What % of mtl has good access (scores 4-5)?
count_good = count[4] + count[5]
total = len(pts_in_boundary)
percentage_good = (count_good / total) * 100
print(f"{percentage_good:.1f}% of Montreal has good access to grocery stores \n")

# What % of mtl has poor access (scores 1-2)?
count_poor = count[1] + count[2]
percentage_poor = (count_poor / total) * 100
print(f"{percentage_poor:.1f}% of Montreal has poor access to grocery stores \n")

# What is the average accessibility score?
average_score = pts_in_boundary['accessibility_score'].mean()
print(f"Average accessibility score: {average_score:.2f} \n")

pts_for_viz = pts_in_boundary.to_crs('EPSG:4326')

#prep data for heatmap
heat_data = []
for index, row in pts_for_viz.iterrows():
    lat = row.geometry.y
    lon = row.geometry.x
    score = row['accessibility_score']
    heat_data.append([lat, lon, score])

#print(heat_data[:5])

heat_layer = folium.FeatureGroup(name="heat map")

HeatMap(heat_data, radius=25, blur=20).add_to(heat_layer)

heat_layer.add_to(m)
folium.LayerControl().add_to(m)

#SOCIOECONOMIC ANALYSIS (INCOME)

income_geodata = geopandas.read_file("geos.geojson")
income_csv = pd.read_csv('data.csv')

#merge both dataframes
income_geodata['id'] = income_geodata['id'].astype(str)
income_csv['GeoUID'] = income_csv['GeoUID'].astype(str)

income_data = pd.merge(income_geodata, income_csv, left_on='id', right_on='GeoUID')

print(income_data.head())
print(income_data.columns)

m.save("index.html")