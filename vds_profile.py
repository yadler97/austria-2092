import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely import wkt
from matplotlib.colors import TwoSlopeNorm
import seaborn as sns
import numpy as np
import matplotlib.cm as cm

data = pd.read_csv("wrangled_data/merged_data.csv", sep=";")

# Filter df for Namlos
namlos = data[data['name'] == 'Wien 10., Favoriten']

if namlos.empty:
    print("Municipality 'Namlos' not found in the data.")
else:
    # Select age columns
    age_cols = [
        "age_0_4", "age_5_9", "age_10_14", "age_15_19",
        "age_20_24", "age_25_29", "age_30_34", "age_35_39",
        "age_40_44", "age_45_49", "age_50_54", "age_55_59",
        "age_60_64", "age_65_69", "age_70_74", "age_75_79",
        "age_80_84", "age_85_plus"
    ]
    
    # Extract values
    age_values = namlos[age_cols].values.flatten()
    
    # Plot
    plt.figure(figsize=(12, 6))
    plt.bar(age_cols, age_values, color='skyblue')
    plt.xticks(rotation=45)
    plt.ylabel("Population")
    plt.title("Population by Age Group in Wien 10., Favoriten (2025)")
    plt.tight_layout()
    plt.show()


# Plot
data['geometry'] = data['geometry'].apply(lambda x: wkt.loads(x) if pd.notnull(x) else None)
data = gpd.GeoDataFrame(data, geometry='geometry', crs="EPSG:31287")

data['foreigner_share'] = data['foreigner_population_2025'] / data['total_population_2025']
data['death_rate'] = data['died_abs'] / data['total_population_2025']
data['birth_rate'] = data['born_abs'] / data['total_population_2025']
data['pop_change_rate'] = (
    data['total_population_2025'] - data['total_population_2002']
) / data['total_population_2002']
data['foreigner_share_2002'] = data['foreigner_population_2002'] / data['total_population_2002']

# data = data[data['g_id'].astype(str).str.startswith(('706', '708', '8'))]

norm = TwoSlopeNorm(vmin=data['pop_change_rate'].min(),
                    vcenter=0,
                    vmax=data['pop_change_rate'].max())

fig, ax = plt.subplots(1, 1, figsize=(12, 12))
data.plot(column='pop_change_rate',
            ax=ax,
            legend=True,
            legend_kwds={
                "shrink": 0.4
            },
            norm=norm,
            cmap='coolwarm')
ax.set_title("Population Change per Municipality (2002 vs 2025)", fontsize=16)
ax.axis('off')

plt.show()

x = data['avg_age'].values
y = data['foreigner_share'].values

plt.figure(figsize=(10,6))

# Hexbin plot
hb = plt.hexbin(
    x, 
    y, 
    gridsize=50,
    cmap='viridis',
    mincnt=1
)

# Fit a linear regression
mask = ~np.isnan(x) & ~np.isnan(y)  # ignore NaNs
coeffs = np.polyfit(x[mask], y[mask], deg=1)  # linear regression
y_fit = np.polyval(coeffs, x)

# Plot regression line
plt.plot(x, y_fit, color='red', linewidth=2, label=f"y = {coeffs[0]:.3f}x + {coeffs[1]:.3f}")

plt.xlabel("Average Age")
plt.ylabel("Share of Foreign Citizens")
plt.title("Hexbin of Average Age vs Share of Foreign Citizens")
plt.colorbar(hb, label='Number of Municipalities')
plt.legend()
plt.show()

# predicted change from natural + migration
data['predicted_change'] = data['saldo_natural_change_abs'] + data['saldo_migration_abs']

x = data['predicted_change']
y = data['population_change_abs']
pop_size = data['total_population_2024']
names = data['name']

# Zoom range for small towns
zoom_range = 50
mask = (x >= -zoom_range) & (x <= zoom_range) & (y >= -zoom_range) & (y <= zoom_range)
x_zoom = x[mask]
y_zoom = y[mask]
pop_zoom = pop_size[mask]
names_zoom = names[mask]

# Compute residuals
residuals = y_zoom - x_zoom

plt.figure(figsize=(10,6))
plt.scatter(
    x_zoom, y_zoom,
    #cmap='viridis',
    s=30,
    alpha=0.7,
    edgecolor='k'
)

# Perfect prediction line
lims = [min(x_zoom.min(), y_zoom.min()), max(x_zoom.max(), y_zoom.max())]
plt.plot(lims, lims, 'r--', label='Perfect Prediction')

# Residuals (vertical dotted lines)
for xi, yi in zip(x_zoom, y_zoom):
    plt.plot([xi, xi], [xi, yi], 'k:', lw=0.8, alpha=0.5)

# Label top 5 largest residuals
top_residuals_idx = np.argsort(np.abs(residuals))[-5:]
for idx in top_residuals_idx:
    plt.text(
        x_zoom.iloc[idx], y_zoom.iloc[idx], 
        names_zoom.iloc[idx],
        fontsize=9, fontweight='bold', color='darkred',
        ha='right', va='bottom'
    )

plt.xlabel("Predicted Absolute Population Change")
plt.ylabel("Actual Absolute Population Change")
plt.title("Predicted vs Absolute Population Change per Municipality (2024-2025)")
plt.legend()
plt.grid(True, ls="--", lw=0.5)
plt.show()

# Define age columns
age_columns = [
    'age_0_19_share', 
    'age_20_64_share', 
    'age_65_plus_share'
]

# Districts of Vienna (IDs 901 to 923)
regions_of_interest = [str(i) for i in range(901, 924)]

# Filter and enforce order
df_regions = data[data['id'].isin(regions_of_interest)]
df_regions = df_regions.set_index('id').loc[regions_of_interest].reset_index()

# Optional: shorter labels for readability
df_regions['label'] = df_regions['name'].str.replace("Wien ", "", regex=False)

# --- Figure ---
fig, ax = plt.subplots(figsize=(18, 9))

# --- Stacked bars ---
bottom = np.zeros(len(df_regions))

viridis_colors = [cm.viridis(0.1), cm.viridis(0.5), cm.viridis(0.9)]

for col, color_val in zip(age_columns, viridis_colors):
    ax.bar(
        df_regions['label'],
        df_regions[col],
        bottom=bottom,
        label=col,
        color=color_val,
        alpha=0.85,
        edgecolor='white',
        linewidth=0.5
    )
    bottom += df_regions[col]

ax.set_xlabel("District", fontsize=12)
ax.set_ylabel("Population Share (%)", fontsize=12)
ax.set_title("Population by Age Group per Viennese District", fontsize=16, pad=20)

plt.xticks(rotation=75, ha='right', fontsize=10)
ax.set_ylim(0, 100)

ax.yaxis.grid(True, linestyle="--", linewidth=1.5, alpha=1, dashes=(6, 10))
ax.set_axisbelow(False)

# --- Secondary axis for avg_age ---
ax2 = ax.twinx()
ax2.plot(
    df_regions['label'], 
    df_regions['avg_age'],
    marker='o',
    linestyle='-',
    linewidth=3.2,
    markersize=8,
    color='black',
    label='avg_age'
)

# --- Linear mapping constants ---
a = 0.1   # slope: +0.1 years per 1%
b = 38    # intercept: when percent = 0%

# Primary axis limits (in percent)
y1_min, y1_max = ax.get_ylim()

# Compute corresponding secondary axis limits using the mapping
y2_min = a * y1_min + b
y2_max = a * y1_max + b

ax2.set_ylim(y2_min, y2_max)

ax2.set_ylabel("Average Age (years)", fontsize=12)

# --- Legend ---
bars_handles, bars_labels = ax.get_legend_handles_labels()
line_handles, line_labels = ax2.get_legend_handles_labels()

ax.legend(
    bars_handles + line_handles,
    bars_labels + line_labels,
    title="Age Groups / Average Age",
    loc='upper left',
    bbox_to_anchor=(1.01, 1)
)

plt.tight_layout()
plt.show()

