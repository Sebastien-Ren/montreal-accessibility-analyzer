import pandas
import folium
import osmnx
import geopandas
import matplotlib

m = folium.Map(location=(45.5019, -73.5674), control_scale=True, zoom_start=15)

m.save("index.html")