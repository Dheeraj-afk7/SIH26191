"""Detailed Census structure inspection."""
import pandas as pd

xl = pd.ExcelFile('data/raw/habitations/PCA_CDB-0503-F-Census.xlsx')
df = xl.parse(xl.sheet_names[0])

print('=== LEVEL COLUMN ANALYSIS ===')
print(f'Level unique values: {df["Level"].unique().tolist()}')
print(f'Level value counts:')
print(df['Level'].value_counts())

print()
print('=== TOWN/VILLAGE VALUE = 0 (block/sub-district headers) ===')
header_rows = df[df['Town/Village'] == 0]
print(f'Count: {len(header_rows)}')
print(header_rows[['CD Block', 'Town/Village', 'Level', 'Name', 'TOT_P']].to_string())

print()
print('=== VILLAGE LEVEL RECORDS ONLY ===')
villages = df[df['Level'] == 'VILLAGE']
print(f'Count: {len(villages)}')
print(f'Zero TOT_P in villages: {len(villages[villages["TOT_P"] == 0])}')
print(f'Inhabited villages (TOT_P > 0): {len(villages[villages["TOT_P"] > 0])}')

print()
print('=== TRU BREAKDOWN FOR VILLAGE LEVEL ===')
print(df[df['Level'] == 'VILLAGE']['TRU'].value_counts())

print()
print('=== WHAT IS "Level" for village rows? ===')
print(df[df['Town/Village'] > 0][['Level', 'TRU', 'Town/Village', 'Name', 'TOT_P']].head(20).to_string())
