from shiny import App, render, ui, reactive
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import tempfile

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

# Define get_color_and_width function
def get_color_and_width(avg_migration_index):
    if avg_migration_index <= 300:
        return 'lightgrey', 0.3
    elif avg_migration_index <= 1000:
        return 'lightgreen', 1.5
    elif avg_migration_index <= 2500:
        return 'orange', 2.0
    else:
        return 'red', 3.0

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
    @render.image
    def migration_plot():
        # Filter data for the selected year
        year_data = filtered_data.get()
        
        # Create the plot with a larger size
        fig=plt.figure(figsize=(15, 18))
        ax = plt.gca()
        city_boundaries.plot(ax=ax, color="none", edgecolor="black")
        
        # Add city names and centers
        for idx, row in city_boundaries.iterrows():
            ax.text(row.geometry.centroid.x, row.geometry.centroid.y, row['cityE'], fontsize=12,
                    ha='center', va='center', color='black', zorder=6)
            ax.plot(row.geometry.centroid.x, row.geometry.centroid.y, 'o', color='red', markersize=8, zorder=4)
        
        # Plot migration lines
        for _, row in year_data.iterrows():
            line = row['geometry']
            color, width = get_color_and_width(row['avg_migration_index'])
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
        
        # Save the plot to a temporary file
        tmpfile = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        fig.savefig(tmpfile.name)
        plt.close(fig)
        
        return {"src": tmpfile.name, "width": "70%", "height": "auto"}

# Run the app
app = App(app_ui, server)