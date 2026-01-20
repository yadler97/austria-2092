import pandas as pd
import geopandas as gpd
from shapely import wkt

data = pd.read_csv("wrangled_data/merged_data.csv", sep=";")

data['geometry'] = data['geometry'].apply(lambda x: wkt.loads(x) if pd.notnull(x) else None)
data = gpd.GeoDataFrame(data, geometry='geometry', crs="EPSG:31287")

# reproject to WGS84
data_web = data.to_crs(epsg=4326)
data_web.to_file("municipalities.geojson", driver="GeoJSON", encoding="utf-8")