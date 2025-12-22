import pandas
import folium
import osmnx
import geopandas
import matplotlib

m = folium.Map(location=(45.5019, -73.5674), control_scale=True, zoom_start=15)

mtl_boundaries = osmnx.geocoder.geocode_to_gdf("Montreal", which_result=None)

#print(mtl_boundaries.head())

folium.GeoJson(mtl_boundaries).add_to(m)

mtl_pts_of_interest = osmnx.features.features_from_place("Montreal", {'shop': ['supermarket','grocery']}, which_result=None)

#filter for only points, no polygons for now
mtl_pts_of_interest = mtl_pts_of_interest[mtl_pts_of_interest.geometry.type == 'Point']

print(f"Found {len(mtl_pts_of_interest)} stores")
#print(mtl_pts_of_interest.head())

for index, row in mtl_pts_of_interest.iterrows():
    y = row.geometry.y
    x = row.geometry.x

    folium.Marker(location=[y, x]).add_to(m)


m.save("index.html")