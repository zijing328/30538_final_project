from shiny import App, render, ui, reactive
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# Load data
df = pd.read_excel("/Users/shenzekai/Documents/GitHub/30538_final_project/avg_migration_18-23.xlsx")
city_boundaries = gpd.read_file("/Users/shenzekai/Documents/GitHub/30538_final_project/长三角城市数据/长三角地市_1.shp").to_crs(epsg=3857)

# Prepare city center dictionary
city_boundaries['centroid'] = city_boundaries['geometry'].centroid
city_centers = city_boundaries.set_index('cityE')['centroid'].to_dict()

# Add geometry for migration lines
def create_linestring(row):
    point1 = city_centers[row['city1']]
    point2 = city_centers[row['city2']]
    return Line2D([point1.x, point2.x], [point1.y, point2.y])

df['geometry'] = df.apply(lambda row: create_linestring(row), axis=1)

# Define color mapping for imbalance index ranges
color_map = {
    '0-300': 'lightgrey',
    '300-1000': 'lightgreen',
    '1000-2500': 'orange',
    '2500-9000': 'red',
}

width_map = {
    '0-300': 0.3,
    '300-1000': 1.5,
    '1000-2500': 2.0,
    '2500-9000': 2.5,
}
# Categorize imbalance values
def get_color_and_width(value):
    if 0 <= value < 300:
        return color_map['0-300'], width_map['0-300']
    elif 300 <= value < 1000:
        return color_map['300-1000'], width_map['300-1000']
    elif 1000 <= value < 2500:
        return color_map['1000-2500'], width_map['1000-2500']
    elif 2500 <= value < 9000:
        return color_map['2500-9000'], width_map['2500-9000']
    return 'grey', 0.5  # Default color for any value outside specified ranges

df['color'], df['width'] = zip(*df['avg_migration_index'].apply(get_color_and_width))









# UI definition
app_ui = ui.page_fluid(
    ui.h2("Average Migration Network (2018–2023)"),
    ui.input_slider("year", "Select Year:", min=2018, max=2023, value=2018),
    ui.output_plot("migration_plot")
)

# Server logic
def server(input, output, session):
    filtered_data = reactive.Value(df[df['year'] == 2018])
    
    @reactive.Effect
    def update_filtered_data():
        filtered_data.set(df[df['year'] == input.year()])
    
    @output
    @render.plot
    def migration_plot():
        # Filter data for the selected year
        year_data = filtered_data.get()
        
        # Create the plot
        fig, ax = plt.subplots(1, figsize=(10, 12))
        city_boundaries.plot(ax=ax, color="none", edgecolor="black")
        
        # Add city names and centers
        for idx, row in city_boundaries.iterrows():
            ax.text(row.geometry.centroid.x, row.geometry.centroid.y, row['cityE'], fontsize=9,
                    ha='center', va='center', color='black', zorder=6)
            ax.plot(row.geometry.centroid.x, row.geometry.centroid.y, 'o', color='red', markersize=5, zorder=4)
        
        # Plot migration lines
        for _, row in year_data.iterrows():
            line = row['geometry']
            color = row['color']
            width = row['width']
            ax.plot(line.get_xdata(), line.get_ydata(), color=color, linewidth=width)
        
        # Add legend
        legend_elements = [
            Line2D([0], [0], color='lightgrey', lw=0.3, label='0-300'),
            Line2D([0], [0], color='lightgreen', lw=1.5, label='300-1000'),
            Line2D([0], [0], color='orange', lw=2.0, label='1000-2500'),
            Line2D([0], [0], color='red', lw=2.5, label='2500-9000')
        ]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=10, title="Migration Index")
        
        # Customize plot
        ax.set_title(f"Average Migration Network - Year {input.year()}", loc="center")
        ax.axis("off")
        
        return fig

# Run the app
app = App(app_ui, server)
