import pandas
import folium
import osmnx
import geopandas
import matplotlib

m = folium.Map(location=(45.5019, -73.5674), control_scale=True, zoom_start=15)

mtl_boundaries = osmnx.geocoder.geocode_to_gdf("Montreal", which_result=None)

#print(mtl_boundaries.head())

folium.GeoJson(mtl_boundaries).add_to(m)

m.save("index.html")