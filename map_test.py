import pandas as pd
import numpy as np
import folium
import osmnx
import geopandas
import matplotlib
from shapely import Point

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



#adding grid points to folium map to visualize, icon color as green
for row in pts_in_boundary.itertuples():
    folium.CircleMarker(
        location=[row.geometry.y, row.geometry.x],
        radius=5,
        color="green",
        fill=True,
        fillColor="green",
        fillOpacity=0.6
    ).add_to(m)

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

folium.LayerControl().add_to(m)



m.save("index.html")