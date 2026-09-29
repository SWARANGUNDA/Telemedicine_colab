import pandas as pd
import numpy as np

df = pd.read_csv('Clinical_Dataset.csv')

print('=' * 70)
print('DATASET OVERVIEW')
print('=' * 70)
print(f'Shape: {df.shape[0]:,} rows x {df.shape[1]} columns')

features = ['Age','Gender','Height_cm','Weight_kg','BMI','Waist_Circumference_cm',
            'Systolic_BP','Diastolic_BP','Fasting_Blood_Glucose','HbA1c',
            'LDL_Cholesterol','HDL_Cholesterol','Triglycerides','ALT','AST',
            'Family_History_Diabetes','Family_History_Obesity',
            'Family_History_Hypertension','Family_History_NAFLD']
labels = ['Type2_Diabetes','Prediabetes','Obesity','Metabolic_Syndrome','NAFLD','Healthy']
print(f'Input features: {len(features)}')
print(f'Target labels: {len(labels)}')

print('\n--- MISSING VALUES ---')
for f in features:
    miss = df[f].isnull().sum()
    if miss > 0:
        pct = df[f].isnull().mean() * 100
        print(f'  {f}: {miss:,} ({pct:.1f}%)')
total_miss = df[features].isnull().sum().sum()
total_cells = df[features].size
print(f'  Total: {total_miss:,} / {total_cells:,} ({total_miss/total_cells*100:.1f}%)')

print('\n--- LABEL DISTRIBUTION ---')
for l in labels:
    pos = int(df[l].sum())
    neg = len(df) - pos
    pct = df[l].mean() * 100
    print(f'  {l}: {pos:,} pos ({pct:.1f}%) | {neg:,} neg ({100-pct:.1f}%)')

print('\n--- MULTI-LABEL STATS ---')
disease_cols = ['Type2_Diabetes','Prediabetes','Obesity','Metabolic_Syndrome','NAFLD']
n_diseases = df[disease_cols].sum(axis=1)
print('Diseases per patient:')
for i in range(6):
    cnt = int((n_diseases == i).sum())
    print(f'  {i} diseases: {cnt:,} ({cnt/len(df)*100:.1f}%)')

print('\n--- CO-OCCURRENCE (% of col that also has row) ---')
header = '                      ' + '  '.join([d[:6] for d in disease_cols])
print(header)
for d1 in disease_cols:
    row_vals = []
    for d2 in disease_cols:
        if d1 == d2:
            row_vals.append('  -  ')
        else:
            overlap = ((df[d1]==1) & (df[d2]==1)).sum()
            total_d2 = max((df[d2]==1).sum(), 1)
            row_vals.append(f'{overlap/total_d2*100:5.1f}')
    print(f'  {d1:20s}: ' + '  '.join(row_vals))

print('\n--- CLASS IMBALANCE RATIO ---')
for l in labels:
    majority = max(df[l].mean(), 1-df[l].mean())
    minority = min(df[l].mean(), 1-df[l].mean())
    ratio = majority / minority
    print(f'  {l}: {ratio:.1f}:1')

print('\n--- FEATURE CORRELATIONS WITH LABELS ---')
numeric_feats = ['Age','BMI','Waist_Circumference_cm','Systolic_BP','Diastolic_BP',
                 'Fasting_Blood_Glucose','HbA1c','LDL_Cholesterol','HDL_Cholesterol',
                 'Triglycerides','ALT','AST']
for l in disease_cols:
    top_corrs = []
    for f in numeric_feats:
        valid = df[[f, l]].dropna()
        r = valid[f].corr(valid[l])
        top_corrs.append((f, r))
    top_corrs.sort(key=lambda x: abs(x[1]), reverse=True)
    top3 = ', '.join([f'{name}({r:+.2f})' for name, r in top_corrs[:3]])
    print(f'  {l}: {top3}')
