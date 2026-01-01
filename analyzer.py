import pandas as pd
import numpy as np
import folium
import osmnx
import geopandas
from shapely import Point
from folium.plugins import HeatMap
from math import ceil

def get_city_boundary(city_name):
    boundary_box = osmnx.geocode_to_gdf(city_name, which_result=None)
    return boundary_box.to_crs(3857)

def create_grid(boundary, spacing_meters = 500):
    boundary_box = boundary.to_crs(3857)

    min_x = boundary_box.bounds.minx.iloc[0]
    max_x = boundary_box.bounds.maxx.iloc[0]
    min_y = boundary_box.bounds.miny.iloc[0]
    max_y = boundary_box.bounds.maxy.iloc[0]

    width = max_x - min_x
    height = max_y - min_y

    num_pts_width = ceil(width / spacing_meters) + 1
    num_pts_height = ceil(height / spacing_meters) + 1

    x_values = np.linspace(min_x, max_x, num_pts_width)
    y_values = np.linspace(min_y, max_y, num_pts_height)

    coord_pairs = np.array(np.meshgrid(x_values, y_values)).T.reshape(-1, 2)
    list_points = [Point(x, y) for x, y in coord_pairs]

    grid = geopandas.GeoDataFrame(crs="EPSG:3857", geometry=list_points)

    return grid.sjoin(boundary, how="inner")

def get_grocery_stores(city_boundary):
    boundary_latlon = city_boundary.to_crs(4326)
    geom = boundary_latlon.geometry.iloc[0]
    grocery_pts = osmnx.features.features_from_polygon(geom, {'shop': ['supermarket','grocery']})

    #filter for only pts, no polygons
    grocery_pts = grocery_pts[grocery_pts.geometry.type == 'Point']

    return grocery_pts

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

def calculate_accessibility(city_pts, grocery_pts):
    pts_metric = city_pts.to_crs(3857)
    grocery_metric = grocery_pts.to_crs(3857)

    distances_list = []
    for point in pts_metric.geometry:
        temp_distances = []
        for grocery in grocery_metric.geometry:
            temp_distances.append(point.distance(grocery))

        distances_list.append(min(temp_distances))
    
    pts_metric['nearest_distance'] = distances_list
    pts_metric['accessibility_score'] = pts_metric['nearest_distance'].apply(scoring_distance)

    return pts_metric

def calculate_income_statistics(city_name, grid_gdf):
    if not city_name.lower() == "montreal":
        print("income analysis only works for Montreal currently \n")
        return None
    else:
        try:
            income_geodata = geopandas.read_file("geos.geojson")
            income_csv = pd.read_csv('data.csv')
        except FileNotFoundError:
            print(f"Income data files not found for {city_name}")
            return None

        #merge both dataframes
        income_geodata['id'] = income_geodata['id'].astype(str)
        income_csv['GeoUID'] = income_csv['GeoUID'].astype(str)

        income_data = pd.merge(income_geodata, income_csv, left_on='id', right_on='GeoUID')

        #convert back to geodataframe
        income_data = geopandas.GeoDataFrame(income_data, geometry='geometry', crs='EPSG:4326')
        grid_gdf = grid_gdf.to_crs(4326)

        if 'index_right' in grid_gdf.columns:
            grid_gdf = grid_gdf.drop(columns=['index_right'])

        #spatial join
        pts_with_income = geopandas.sjoin(grid_gdf, income_data, how='left', predicate='within')

        income_col = 'v_CA21_560: Median total income in 2020 among recipients ($)'

        #removing NaN rows
        pts_with_income_clean = pts_with_income.dropna(subset=[income_col])

        #get income thresholds
        income_25th = pts_with_income_clean[income_col].quantile(0.25)
        income_75th = pts_with_income_clean[income_col].quantile(0.75)

        #filter data into two groups
        low_income_pts = pts_with_income_clean[pts_with_income_clean[income_col] < income_25th]
        high_income_pts = pts_with_income_clean[pts_with_income_clean[income_col] > income_75th]

        low_income_avg = low_income_pts['accessibility_score'].mean()
        high_income_avg = high_income_pts['accessibility_score'].mean()

        #simple analytics
        raw_diff = abs(low_income_avg - high_income_avg)
        perc_diff = abs((high_income_avg - low_income_avg) / low_income_avg) * 100

        #remove NaN income tracts
        income_data_clean = income_data.dropna(subset=[income_col])

        income_data_clean = income_data_clean.rename(columns={
            income_col: 'median_income'
        })

        return {
            'statistics': {
                'low_income_avg_score': low_income_avg,
                'high_income_avg_score': high_income_avg,
                'percentage_difference': perc_diff,
                'income_25th': income_25th,
                'income_75th': income_75th
            },
            'income_geodata': income_data_clean
            }

def create_map(boundary_gdf, grid_gdf, stores_gdf, city_name, income_data = None, output_file=None):
    
    #convert to lat/lon for folium
    boundary_latlon = boundary_gdf.to_crs(4326)
    grid_latlon = grid_gdf.to_crs(4326)
    
    #getting map center
    centroid = boundary_gdf.to_crs(3857).centroid.to_crs(4326).iloc[0]
    center = [centroid.y, centroid.x]

    m = folium.Map(location=center, control_scale=True)

    #fit bounds to city
    bounds = boundary_latlon.total_bounds
    sw = [bounds[1], bounds[0]]
    ne = [bounds[3], bounds[2]]
    m.fit_bounds([sw, ne])

    #add boundary layer
    boundary_layer = folium.FeatureGroup(name="boundary")
    folium.GeoJson(boundary_latlon).add_to(boundary_layer)
    boundary_layer.add_to(m)

    #add grid points layer
    points_layer = folium.FeatureGroup(name="grid points", show=False)
    for row in grid_latlon.itertuples():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=5,
            color='green',
            fill=True,
            fillColor='green',
            fillOpacity=0.6
        ).add_to(points_layer)
    points_layer.add_to(m)

    #add grocery layer
    grocery_layer = folium.FeatureGroup(name="grocery stores", show=False)
    for index, row in stores_gdf.iterrows():
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
        
        folium.Marker(location=[y, x], popup=popup_text).add_to(grocery_layer)

    grocery_layer.add_to(m)

    #add heatmap layer
    heat_data = []
    for index, row in grid_latlon.iterrows():
        lat = row.geometry.y
        lon = row.geometry.x
        score = row['accessibility_score']
        heat_data.append([lat, lon, score])

    heat_layer = folium.FeatureGroup(name="heat map")

    HeatMap(heat_data, radius=25, blur=20).add_to(heat_layer)
    heat_layer.add_to(m)

    #only add choropleth if income data exists
    if income_data is not None:
        folium.Choropleth(income_data, income_data[['GeoUID', 'median_income']], ['GeoUID', 'median_income'], key_on='feature.properties.GeoUID', fill_color='BuPu', name="Median Income", legend_name="Median Household Income ($)", overlay=True, control=True).add_to(m)

    #add layer control
    folium.LayerControl().add_to(m)

    #save map
    if output_file is None:
        output_file = f"{city_name.lower().replace(' ', '_')}_map.html"
    m.save(output_file)
    print(f"Map saved to {output_file}")

    return m

def analyze_city(name):
    city_boundary = get_city_boundary(name)
    city_grid = create_grid(city_boundary)
    city_stores = get_grocery_stores(city_boundary)
    city_grid_scored = calculate_accessibility(city_grid, city_stores)
    city_income_analysis = calculate_income_statistics(name, city_grid_scored)

    if city_income_analysis is not None:
        stats = city_income_analysis['statistics']
        print(f"\nINCOME DISPARITY ANALYSIS:")
        print(f"Low-income areas (<${stats['income_25th']:.0f}): avg score {stats['low_income_avg_score']:.2f}")
        print(f"High-income areas (>${stats['income_75th']:.0f}): avg score {stats['high_income_avg_score']:.2f}")
        print(f"High-income areas have {stats['percentage_difference']:.1f}% worse accessibility \n")
        map = create_map(city_boundary, city_grid_scored, city_stores, name, income_data=city_income_analysis['income_geodata'])
    else:
        map = create_map(city_boundary, city_grid_scored, city_stores, name)
    

    print(f"KEY FINDINGS for {name}: \n")

    # How many pts in each score category?
    count = city_grid_scored['accessibility_score'].value_counts()
    print(f"# of pts in each score category: \n {count} \n")

    # What % of city has good access (scores 4-5)?
    count_good = count[4] + count[5]
    total = len(city_grid_scored)
    percentage_good = (count_good / total) * 100
    print(f"{percentage_good:.1f}% of {name} has good access to grocery stores \n")

    # What % of city has poor access (scores 1-2)?
    count_poor = count[1] + count[2]
    percentage_poor = (count_poor / total) * 100
    print(f"{percentage_poor:.1f}% of {name} has poor access to grocery stores \n")

    # What is the average accessibility score?
    average_score = city_grid_scored['accessibility_score'].mean()
    print(f"Average accessibility score: {average_score:.2f} \n")

analyze_city("montreal")

    