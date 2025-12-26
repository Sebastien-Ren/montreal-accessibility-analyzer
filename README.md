# Montreal Accessibility Analyzer

![Accessibility Map](images/screenshot.png)

Food accessibility is a critical urban planning issue that directly impacts community health and equity.
This project analyzes grocery store accessibility across Montreal to identify which neighborhoods are well-served and which face barriers to accessing fresh food.

## Features

- **Interactive accessibility heatmap** showing grocery access patterns across Montreal
- **827 analysis points** covering the entire city boundary
- **Distance calculations** from every location to nearest grocery store
- **5-point accessibility scoring system** (1=Very Poor to 5=Excellent)
- **Toggleable map layers** for boundary, grocery stores, and accessibility heatmap
- **Store information popups** displaying name, brand, and opening hours
- **Statistical analysis** of citywide accessibility patterns

## Data Sources

- **OpenStreetMap (OSM)** - Grocery store locations
- **OSMnx** - Montreal adiministrative boundary and geographic data

## Methodology

1. **Data Collection**: Retrieved Montreal's city boundary and 313 grocery store locations from OpenStreetMap using OSMnx
2. **Grid Generation**: Created 2,500 evenly-spaced points across Montreal's bounding box, filtered to 827 points within city boundaries
3. **Distance Calculation**: Reprojected data to EPSG:32188 (NAD83/Quebec Lambert) for metric calculations; computed straight-line distance from each grid point to nearest store
4. **Accessibility Scoring**: Applied 5-tier scoring system:
   - Score 5 (Excellent): 0-500m
   - Score 4 (Good): 500-1000m
   - Score 3 (Moderate): 1000-2000m
   - Score 2 (Poor): 2000-3000m
   - Score 1 (Very Poor): 3000m+
5. **Visualization**: Generated interactive heatmap using Folium, with color intensity representing accessibility levels

## Key Findings

Montreal's grocery accessibility reveals significant geographic disparities:

**Overall Access:**

- Only **38.3%** of analyzed locations have good accessibility (within 1km of a grocery store)
- **34.9%** face poor accessibility (over 2km from nearest store)
- Average accessibility score: **2.97 out of 5** (just below moderate)

**Distance Patterns:**

- **Minimum:** 35m (some locations adjacent to stores)
- **Maximum:** 10.8km (peripheral areas significantly underserved)
- **Median:** 1.4km (half of Montreal within walking/biking distance)

**Geographic Insights:**

- Central Montreal and major commercial corridors show strong accessibility
- Peripheral neighborhoods and areas near Westmount, Côte-Saint-Luc show accessibility gaps
- Store clustering creates "food oases" while leaving coverage gaps between clusters

## Technologies Used

- **Python 3.x**
- **GeoPandas** - Spatial data manipulation and analysis
- **OSMnx** - OpenStreetMap data retrieval
- **Folium** - Interactive map visualization
- **Folium.plugins.HeatMap** - Accessibility heatmap layer
- **Pandas** - Data processing and analysis
- **NumPy** - Numerical computations and grid generation
- **Shapely** - Geometric operations

## How to Run Locally

### Prerequisities

- Python 3.8 or higher
- pip package manager

### Installation

1. Clone the repository
2. Create and activate virtual environment
3. Install dependencies

### Usage

1. Run the analysis
2. View the results

### Notes

- First run may take a few minutes to download OSM data

## Project Structure

```
montreal-accessibility-analyzer/
├── venv/                      # Virtual environment (not in repo)
├── map_test.py               # Main analysis script
├── index.html                # Generated interactive map
├── README.md                 # Project documentation
└── .gitignore               # Git ignore file
```
