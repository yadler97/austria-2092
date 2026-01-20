import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import geopandas as gpd
from shapely import wkt

data = pd.read_csv("wrangled_data/merged_data.csv", sep=";")

data['foreigner_share'] = data['foreigner_population_2025'] / data['total_population_2025']

# select relevant variables
cluster_df = data[[
    'total_population_2025',
    'avg_age',
    'foreigner_share'
]].dropna()

# log-transform population to reduce skew
cluster_df['log_population'] = np.log10(cluster_df['total_population_2025'])

X = cluster_df[['log_population', 'avg_age', 'foreigner_share']]

# standardize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)



kmeans = KMeans(n_clusters=3, random_state=42)
cluster_df['cluster'] = kmeans.fit_predict(X_scaled)

# merge back into main dataframe
data = data.merge(
    cluster_df[['cluster']],
    left_index=True,
    right_index=True,
    how='left'
)



data["cluster_str"] = data["cluster"].astype(str)
cluster_labels = {
    "0": "Rural",
    "1": "Growth",
    "2": "Urban",
    "3": "Medium"
}

data["cluster_label"] = data["cluster_str"].map(cluster_labels)

import matplotlib.pyplot as plt
import matplotlib.cm as cm

plt.figure(figsize=(10, 6))

# choose a colormap
cmap = cm.get_cmap('tab10', 3)  # 3 discrete colors

# scatter with colormap
scatter = plt.scatter(
    cluster_df['log_population'],
    cluster_df['avg_age'],
    c=cluster_df['cluster'],  # numeric clusters
    cmap=cmap,
    s=30,
    alpha=0.8
)

plt.xlabel('Log10 Population (2025)')
plt.ylabel('Average Age')
plt.title('Urbanization Clusters of Austrian Municipalities')

# create a legend with labels
cluster_labels = ['Rural', 'Growth', 'Urban']
handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=cmap(i), markersize=8)
           for i in range(3)]
plt.legend(handles, cluster_labels, title='Cluster')
plt.show()



data['geometry'] = data['geometry'].apply(lambda x: wkt.loads(x) if pd.notnull(x) else None)
data = gpd.GeoDataFrame(data, geometry='geometry', crs="EPSG:31287")

fig, ax = plt.subplots(1, 1, figsize=(10, 10))

# define distinct colors for clusters
color_dict = {
    'Rural': '#8C564B',
    'Growth': '#1F77B4',
    'Urban': '#BCBD22',
}

# map colors
data['color'] = data['cluster_label'].map(color_dict)

data.plot(
    color=data['color'],  # use mapped colors
    ax=ax,
    legend=False          # we will create a manual legend
)

# create a manual legend
import matplotlib.patches as mpatches
handles = [mpatches.Patch(color=color, label=label) for label, color in color_dict.items()]
ax.legend(handles=handles, title="Cluster", fontsize=12)

ax.set_title("Spatial Distribution of Municipality Clusters", fontsize=14)
ax.axis("off")
plt.show()