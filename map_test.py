import pandas as pd
import folium
import osmnx
import geopandas
import matplotlib

m = folium.Map(location=(45.5019, -73.5674), control_scale=True, zoom_start=15)

mtl_boundaries = osmnx.geocoder.geocode_to_gdf("Montreal", which_result=None)

boundary = folium.FeatureGroup(name="boundary")



#print(mtl_boundaries.head())

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

print(f"Found {len(mtl_pts_of_interest)} stores")
#print(mtl_pts_of_interest.head())
#print(mtl_pts_of_interest.columns)

folium.LayerControl().add_to(m)

m.save("index.html")