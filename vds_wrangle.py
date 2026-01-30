import pandas as pd
import geopandas as gpd

# AGE DATA

columns = [
    "id",
    "name",
    "total_population_2025",
    "age_0_4",
    "age_5_9",
    "age_10_14",
    "age_15_19",
    "age_20_24",
    "age_25_29",
    "age_30_34",
    "age_35_39",
    "age_40_44",
    "age_45_49",
    "age_50_54",
    "age_55_59",
    "age_60_64",
    "age_65_69",
    "age_70_74",
    "age_75_79",
    "age_80_84",
    "age_85_plus",
    "age_0_19_abs",
    "age_0_19_share",
    "age_20_64_abs",
    "age_20_64_share",
    "age_65_plus_abs",
    "age_65_plus_share",
    "avg_age",
]

age_df = pd.read_excel(
    r"data/Bev_2025_Alter_Geschlecht_Gebietseinheiten.ods",
    engine="odf",
    sheet_name="Insgesamt",
    skiprows=[0, 1, 2, 5, 9, 19, 55, 172, 2265],
    names=columns,
)

age_df.to_csv("wrangled_data/age_data.csv", sep=";", index=False, encoding="utf-8")

# POPULATION CHANGE DATA

columns = [
    "id",
    "name",
    "total_population_2024",
    "population_change_abs",
    "population_change_per_1000",
    "born_abs",
    "died_abs",
    "saldo_natural_change_abs",
    "saldo_natural_change_per_1000",
    "migrated_in_abs",
    "migrated_out_abs",
    "saldo_migration_abs",
    "saldo_migration_per_1000",
    "migrated_in_from_abroad_abs",
    "migrated_out_to_abroad_abs",
    "saldo_migration_abroad_abs",
    "saldo_migration_abroad_per_1000",
    "migrated_in_from_within_country_abs",
    "migrated_out_to_within_country_abs",
    "saldo_migration_within_country_abs",
    "saldo_migration_within_country_per_1000",
    "migration_within_municipality_abs",
    "statistical_adjustment_abs",
    "total_population_2025",
    "married_abs",
    "married_per_1000",
    "divorced_abs",
    "divorced_per_1000",
]

pop_change_df = pd.read_excel(
    r"data/BevVeraend_Komp_Gebietseinh_2024.ods",
    engine="odf",
    skiprows=[0, 1, 2, 3, 4, 7, 11, 21, 57, 174, 2268],
    names=columns,
)

pop_change_df.to_csv("wrangled_data/population_change_data.csv", sep=";", index=False, encoding="utf-8")

# TIME SERIES DATA

columns = [
    "id",
    "name",
    "total_population_2002",
    "total_population_2003",
    "total_population_2004",
    "total_population_2005",
    "total_population_2006",
    "total_population_2007",
    "total_population_2008",
    "total_population_2009",
    "total_population_2010",
    "total_population_2011",
    "total_population_2012",
    "total_population_2013",
    "total_population_2014",
    "total_population_2015",
    "total_population_2016",
    "total_population_2017",
    "total_population_2018",
    "total_population_2019",
    "total_population_2020",
    "total_population_2021",
    "total_population_2022",
    "total_population_2023",
    "total_population_2024",
    "total_population_2025",
]

time_series_df = pd.read_excel(
    r"data/Bev_Zeitreihe_Jahresbeginn_Gebietseinheiten.ods",
    engine="odf",
    sheet_name="Insgesamt",
    skiprows=[0, 3, 7, 17, 53, 170, 2263],
    names=columns,
)

time_series_df.to_csv("wrangled_data/time_series_data.csv", sep=";", index=False, encoding="utf-8")

# TIME SERIES CITIZENS DATA

columns = [
    "id",
    "name",
    "citizen_population_2002",
    "citizen_population_2003",
    "citizen_population_2004",
    "citizen_population_2005",
    "citizen_population_2006",
    "citizen_population_2007",
    "citizen_population_2008",
    "citizen_population_2009",
    "citizen_population_2010",
    "citizen_population_2011",
    "citizen_population_2012",
    "citizen_population_2013",
    "citizen_population_2014",
    "citizen_population_2015",
    "citizen_population_2016",
    "citizen_population_2017",
    "citizen_population_2018",
    "citizen_population_2019",
    "citizen_population_2020",
    "citizen_population_2021",
    "citizen_population_2022",
    "citizen_population_2023",
    "citizen_population_2024",
    "citizen_population_2025",
]

time_series_citizen_df = pd.read_excel(
    r"data/Bev_Zeitreihe_Jahresbeginn_Gebietseinheiten.ods",
    engine="odf",
    sheet_name="Österreichische_Staatsang_",
    skiprows=[0, 3, 7, 17, 53, 170, 2263],
    names=columns,
)

time_series_citizen_df.to_csv("wrangled_data/time_series_citizen_data.csv", sep=";", index=False, encoding="utf-8")

# TIME SERIES FOREIGNER DATA

columns = [
    "id",
    "name",
    "foreigner_population_2002",
    "foreigner_population_2003",
    "foreigner_population_2004",
    "foreigner_population_2005",
    "foreigner_population_2006",
    "foreigner_population_2007",
    "foreigner_population_2008",
    "foreigner_population_2009",
    "foreigner_population_2010",
    "foreigner_population_2011",
    "foreigner_population_2012",
    "foreigner_population_2013",
    "foreigner_population_2014",
    "foreigner_population_2015",
    "foreigner_population_2016",
    "foreigner_population_2017",
    "foreigner_population_2018",
    "foreigner_population_2019",
    "foreigner_population_2020",
    "foreigner_population_2021",
    "foreigner_population_2022",
    "foreigner_population_2023",
    "foreigner_population_2024",
    "foreigner_population_2025",
]

time_series_foreigner_df = pd.read_excel(
    r"data/Bev_Zeitreihe_Jahresbeginn_Gebietseinheiten.ods",
    engine="odf",
    sheet_name="Nichtösterreichische_Staatsang_",
    skiprows=[0, 3, 7, 17, 53, 170, 2263],
    names=columns,
)

time_series_foreigner_df.to_csv("wrangled_data/time_series_foreigner_data.csv", sep=";", index=False, encoding="utf-8")

# SHAPEFILE

gdf_municipalities_path = "data/OGDEXT_GEM_1_STATISTIK_AUSTRIA_20250101/STATISTIK_AUSTRIA_GEM_20250101.shp"
gdf_municipalities = gpd.read_file(gdf_municipalities_path)

gdf_districts_path = "data/OGDEXT_POLBEZ_1_STATISTIK_AUSTRIA_20250101/STATISTIK_AUSTRIA_POLBEZ_20250101.shp"
gdf_districts = gpd.read_file(gdf_districts_path)

age_df['id'] = age_df['id'].astype(str)
pop_change_df['id'] = pop_change_df['id'].astype(str)
time_series_df['id'] = time_series_df['id'].astype(str)
time_series_citizen_df['id'] = time_series_citizen_df['id'].astype(str)
time_series_foreigner_df['id'] = time_series_foreigner_df['id'].astype(str)
gdf_municipalities['g_id'] = gdf_municipalities['g_id'].astype(str)
gdf_districts['g_id'] = gdf_districts['g_id'].astype(str)

gdf_municipalities.loc[gdf_municipalities['g_id'].str.startswith('9'), 'g_id'] = gdf_municipalities.loc[gdf_municipalities['g_id'].str.startswith('9'), 'g_id'].str[:3]

# MERGE EVERYTHING
age_df = age_df.drop(columns=['total_population_2025'], errors='ignore')
merged = age_df.merge(
    pop_change_df.drop(columns=['name', 'total_population_2025', 'total_population_2024'], errors='ignore'),
    on='id',
    how='left'
)
merged = merged.merge(
    time_series_df.drop(columns=['name'], errors='ignore'),
    on='id',
    how='left'
)
merged = merged.merge(
    time_series_citizen_df.drop(columns=['name'], errors='ignore'),
    on='id',
    how='left'
)
merged = merged.merge(
    time_series_foreigner_df.drop(columns=['name'], errors='ignore'),
    on='id',
    how='left'
)

merged = merged.merge(
    gdf_municipalities[['g_id', 'g_name', 'geometry']],
    left_on='id',
    right_on='g_id',
    how='left'
)

merged = merged.merge(
    gdf_districts[['g_id', 'g_name', 'geometry']],
    left_on='id',
    right_on='g_id',
    how='left',
    suffixes=('_mun', '_dist')
)

# Fill missing municipality data with district data
merged['g_id'] = merged['g_id_mun'].fillna(merged['g_id_dist'])
merged['g_name'] = merged['g_name_mun'].fillna(merged['g_name_dist'])
merged['geometry'] = merged['geometry_mun'].fillna(merged['geometry_dist'])

# Drop redundant columns
cols_to_drop = [
    'g_id_mun', 'g_id_dist',
    'g_name_mun', 'g_name_dist',
    'geometry_mun', 'geometry_dist'
]

merged = merged.drop(columns=cols_to_drop)
merged = gpd.GeoDataFrame(merged, geometry='geometry')

merged.to_csv("wrangled_data/merged_data.csv", sep=";", index=False, encoding="utf-8")