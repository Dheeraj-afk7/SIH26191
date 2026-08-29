"""Scratch inspection script for Step 8 inputs."""
import pandas as pd
import geopandas as gpd

# ---- Census Excel ----
xl = pd.ExcelFile('data/raw/habitations/PCA_CDB-0503-F-Census.xlsx')
print('=== CENSUS EXCEL INSPECTION ===')
print(f'Sheet names: {xl.sheet_names}')
df = xl.parse(xl.sheet_names[0])
print(f'Shape: {df.shape}')
print(f'Columns: {df.columns.tolist()}')
print()
print('--- First 3 rows ---')
print(df.head(3).to_string())
print()
print('--- Dtypes ---')
print(df.dtypes)
print()
tv_col = 'Town/Village'
print(f'Null Town/Village: {df[tv_col].isnull().sum()}')
print(f'Sample Town/Village values (first 10): {df[tv_col].dropna().head(10).tolist()}')
print(f'Sample Town/Village dtype: {df[tv_col].dtype}')
print(f'Total rows: {len(df)}')

# Check zero-pop rows
zero_pop = df[df['TOT_P'] == 0]
print(f'Zero population rows: {len(zero_pop)}')
print(f'Inhabited rows (TOT_P > 0): {len(df[df["TOT_P"] > 0])}')

print()
print('=== SHRUG GEOJSON INSPECTION ===')
shrug = gpd.read_file('data/raw/habitations/rudraprayag_census_villages_shrug.geojson')
print(f'Shape: {shrug.shape}')
print(f'Columns: {shrug.columns.tolist()}')
print(f'CRS: {shrug.crs}')
print(f'Geometry types: {shrug.geom_type.unique().tolist()}')
print(f'Sample pc11_village_id (first 10): {shrug["pc11_village_id"].head(10).tolist()}')
print(f'pc11_village_id dtype: {shrug["pc11_village_id"].dtype}')
print(f'Null pc11_village_id: {shrug["pc11_village_id"].isnull().sum()}')
print(f'Duplicate pc11_village_id: {shrug["pc11_village_id"].duplicated().sum()}')
print()
print('--- First 3 rows ---')
print(shrug.head(3).to_string())
