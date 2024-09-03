import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.colors as mcolors
import geopandas as gpd
from sqlalchemy import create_engine
import os

def plot_donors_per_state(db_url):
    # Use 'Agg' backend for Matplotlib
    plt.switch_backend('Agg')
    
    # Set up the database connection
    engine = create_engine(db_url)

    # Query the database to get the Number of Donors per state
    query = """
    SELECT TrackerDonorsStateKey as state, COUNT(tblTrackerDonorDevices.TrackerDonorDevicesKey) as num_devices
    FROM tblTrackerDonorDevices
    JOIN tblTrackerDonors ON tblTrackerDonorDevices.TrackerDonorsKey = tblTrackerDonors.TrackerDonorKey
    GROUP BY TrackerDonorsStateKey
    """
    df = pd.read_sql(query, engine)

    # Path to the shapefile
    shapefile_path = '/Users/sarahjiang/rh-db/static/cb_2018_us_state_500k/cb_2018_us_state_500k.shp'
    gdf = gpd.read_file(shapefile_path)

    # Ensure the columns are in uppercase and strip any leading/trailing spaces
    gdf['STUSPS'] = gdf['STUSPS'].str.upper().str.strip()
    df['state'] = df['state'].str.upper().str.strip()

    # Merge the data with the geopandas dataframe
    gdf = gdf.merge(df, left_on='STUSPS', right_on='state', how='left')

    # Impute zeros for missing values
    gdf['num_devices'] = gdf['num_devices'].fillna(0)

    # Function to create a color column based on the Number of Donors
    def makeColorColumn(gdf, variable, vmin, vmax):
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.Blues)  # Changed colormap to 'Blues'
        gdf['value_determined_color'] = gdf[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)) if pd.notnull(x) else '#FFFFFF')
        return gdf

    # Set the value column to visualize
    variable = 'num_devices'
    vmin, vmax = gdf[variable].min(), gdf[variable].max()
    colormap = "Blues"  # Changed colormap to 'Blues'
    gdf = makeColorColumn(gdf, variable, vmin, vmax)

    # Re-project the geodataframe
    gdf = gdf.to_crs('EPSG:2163')

    # Create figure and axes
    fig, ax = plt.subplots(1, figsize=(6, 4))  # Adjusted figsize for a more reasonable size
    ax.axis('off')

    # Set the font for the visualization
    hfont = {'fontname': 'Helvetica'}

    # Add a title
    ax.set_title('Number of Donors per State', **hfont, fontdict={'fontsize': '12', 'fontweight': '1'})  # Adjusted font size

    # Create colorbar legend
    cbax = fig.add_axes([0.9, 0.2, 0.02, 0.6])  # Adjusted colorbar position and size
    cbax.set_title('Number of Donors\n', **hfont, fontdict={'fontsize': '8', 'fontweight': '0'})  # Adjusted font size

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    fig.colorbar(sm, cax=cbax, format=FuncFormatter(lambda x, _: int(x)))
    tick_font_size = 5  # Adjusted tick font size
    cbax.tick_params(labelsize=tick_font_size)

    # Plot the main map
    gdf.plot(color=gdf['value_determined_color'], linewidth=0.8, ax=ax, edgecolor='0.8')

    # Save the figure
    plot_path = os.path.join('static', 'devices_per_state_heatmap.png')
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")  # Adjusted dpi for better quality
    plt.close(fig)
    return plot_path


def plot_devices_per_state(db_url, shapefile_path, output_path):
    # Set up the database connection
    engine = create_engine(db_url)

    # Query the database to get the number of devices per state
    query = """
    SELECT 
        s.StateAbbrev AS state, 
        COUNT(DISTINCT t.TrackerDonorKey) AS num_donors,
        COUNT(d.TrackerDonorDevicesKey) AS num_devices
    FROM 
        tblTrackerDonorDevices d
    JOIN 
        tblTrackerDonors t ON d.TrackerDonorsKey = t.TrackerDonorKey
    JOIN 
        tlkpState s ON t.TrackerDonorsStateKey = s.StateKey
    GROUP BY 
        s.StateAbbrev
    ORDER BY 
        num_devices DESC;
    """
    df = pd.read_sql(query, engine)

    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Ensure the columns are in uppercase and strip any leading/trailing spaces
    gdf['STUSPS'] = gdf['STUSPS'].str.upper().str.strip()
    df['state'] = df['state'].str.upper().str.strip()

    # Merge the data with the geopandas dataframe
    gdf = gdf.merge(df, left_on='STUSPS', right_on='state', how='left')

    # Function to create a color column based on the number of devices
    def makeColorColumn(gdf, variable, vmin, vmax):
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        mapper = plt.cm.ScalarMappable(norm=norm, cmap=plt.cm.YlOrBr)
        gdf['value_determined_color'] = gdf[variable].apply(lambda x: mcolors.to_hex(mapper.to_rgba(x)) if pd.notnull(x) else '#FFFFFF')
        return gdf

    # Set the value column to visualize
    variable = 'num_devices'
    vmin, vmax = gdf[variable].min(), gdf[variable].max()
    colormap = "YlOrBr"
    gdf = makeColorColumn(gdf, variable, vmin, vmax)

    # Re-project the geodataframe
    gdf = gdf.to_crs('EPSG:2163')

    # Create figure and axes
    fig, ax = plt.subplots(1, figsize=(18, 14))
    ax.axis('off')

    # Set the font for the visualization
    hfont = {'fontname': 'Helvetica'}

    # Add a title
    ax.set_title('Number of Devices per State', **hfont, fontdict={'fontsize': '42', 'fontweight': '1'})

    # Create colorbar legend
    cbax = fig.add_axes([0.89, 0.21, 0.03, 0.31])
    cbax.set_title('Number of Devices\n', **hfont, fontdict={'fontsize': '15', 'fontweight': '0'})

    sm = plt.cm.ScalarMappable(cmap=colormap, norm=plt.Normalize(vmin=vmin, vmax=vmax))
    sm._A = []
    fig.colorbar(sm, cax=cbax, format=FuncFormatter(lambda x, _: int(x)))
    tick_font_size = 16
    cbax.tick_params(labelsize=tick_font_size)

    # Plot the main map
    gdf.plot(color=gdf['value_determined_color'], linewidth=0.8, ax=ax, edgecolor='0.8')

    # Save the plot
    plt.savefig(output_path, bbox_inches='tight')
    plt.close(fig)