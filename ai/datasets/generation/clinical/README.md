# Clinical Dataset Generator

**Generative AI Assisted Telemedicine Platform — Synthetic EHR Dataset Generator**

A production-quality Python project that generates medically realistic synthetic Electronic Health Record (EHR) datasets for training machine learning models to predict metabolic diseases.

---

## Target Diseases

| Disease | Diagnostic Criteria | Target Prevalence |
|---|---|---|
| Type 2 Diabetes | FPG ≥ 126 mg/dL OR HbA1c ≥ 6.5% | ~16% |
| Prediabetes | 100 ≤ FPG ≤ 125 OR 5.7 ≤ HbA1c ≤ 6.4 (and NOT T2D) | ~18% |
| Obesity | BMI ≥ 30 | ~24% |
| Metabolic Syndrome | ≥ 3 of 5 ATP III criteria | ~18% |
| NAFLD (MASLD) | Probabilistic (obesity + TG + ALT + T2D + age) | ~12% |
| Healthy | All disease labels = 0 | ~30% |

---

## Project Architecture

```
clinical_dataset_generator/
├── __init__.py           # Package initialization
├── config.py             # All configurable parameters and medical constants
├── demographics.py       # Patient_ID, Age, Gender generation
├── comorbidity.py        # Metabolic profile assignment, co-occurrence logic
├── anthropometry.py      # Height, Weight, BMI, Waist Circumference
├── vitals.py             # Systolic BP, Diastolic BP
├── laboratory.py         # FPG, HbA1c, LDL, HDL, Triglycerides, ALT, AST
├── family_history.py     # 4 family history binary variables
├── disease_rules.py      # Clinical diagnostic criteria → disease labels
├── noise.py              # Measurement noise injection
├── missingness.py        # Missing value simulation (MAR pattern)
├── validator.py          # Per-patient and dataset-wide validation
├── exporter.py           # CSV export with type enforcement
├── main.py               # Pipeline orchestration and CLI
└── requirements.txt      # Python dependencies
```

### Module Dependency Flow

```
config.py (all modules depend on this)
    │
    ├── demographics.py ──┐
    ├── comorbidity.py ───┤
    │                     ├── anthropometry.py ──┐
    │                     ├── vitals.py ─────────┤
    │                     ├── laboratory.py ─────┤
    │                     └── family_history.py ─┤
    │                                            ├── noise.py
    │                                            ├── disease_rules.py
    │                                            ├── missingness.py
    │                                            ├── validator.py
    │                                            └── exporter.py
    │
    └── main.py (orchestrates all of the above)
```

---

## Installation

### Prerequisites
- Python 3.11 or higher

### Setup

```bash
# Navigate to the project directory
cd clinical_dataset_generator

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Demo Mode (100 patients — for testing)

```bash
python -m clinical_dataset_generator.main --demo
```

This generates `Clinical_Dataset_Demo.csv` with 100 patients for quick testing.

### Full Dataset (20,000 patients)

```bash
python -m clinical_dataset_generator.main
```

This generates `Clinical_Dataset.csv` with 20,000 patients.

### Custom Options

```bash
# Custom size
python -m clinical_dataset_generator.main --size 5000

# Custom random seed
python -m clinical_dataset_generator.main --seed 123

# Custom output file
python -m clinical_dataset_generator.main --output my_dataset.csv

# All options combined
python -m clinical_dataset_generator.main --size 10000 --seed 42 --output output/dataset.csv
```

---

## Dataset Generation Process

The generator follows a strict pipeline to ensure medical realism:

### Step 1: Demographics
- **Patient_ID**: Unique identifiers (P00001 to P20000)
- **Age**: Weighted distribution (18–30: 20%, 31–45: 30%, 46–60: 30%, 61–85: 20%)
- **Gender**: Balanced 50/50 Male/Female

### Step 2: Metabolic Profiles (Internal)
Each patient is assigned an internal metabolic profile that guides feature generation:
- **BMI Category**: Underweight (5%), Normal (31%), Overweight (40%), Obese (24%)
- **Glycemic State**: Normal, Prediabetes, or Diabetes (calibrated for target prevalences)
- **Borderline Flag**: ~15% of patients have values near diagnostic thresholds
- **Outlier Flag**: ~2% have extreme but plausible values

### Step 3: Feature Generation
Features are generated based on the metabolic profile with medically realistic correlations:
- Higher BMI → Higher BP, Glucose, Triglycerides, ALT; Lower HDL
- Older Age → Higher BP, Higher diabetes risk
- FPG and HbA1c are strongly correlated
- Waist tracks BMI closely (gender-specific)
- TG and HDL inversely correlated

### Step 4: Noise Injection
Small Gaussian noise mimics real measurement variability:
- Height ±0.5 cm, Weight ±1 kg, BP ±3 mmHg
- FPG ±5 mg/dL, HbA1c ±0.2%, Lipids ±3–8 mg/dL, Liver enzymes ±3 U/L
- BMI is recomputed from noisy Height/Weight

### Step 5: Disease Label Assignment
Labels are derived deterministically from features using clinical criteria:
- **T2D**: FPG ≥ 126 OR HbA1c ≥ 6.5 (ADA)
- **Prediabetes**: (100 ≤ FPG ≤ 125 OR 5.7 ≤ HbA1c ≤ 6.4) AND NOT T2D
- **Obesity**: BMI ≥ 30 (WHO/CDC)
- **MetS**: ≥ 3 of 5 ATP III criteria
- **NAFLD**: Probabilistic risk scoring (obesity + TG + ALT + T2D + age)
- **Healthy**: All disease labels = 0

### Step 6: Missing Value Simulation
Optional features receive controlled missingness (MAR pattern):
- Waist ~3%, Lipids ~2%, Liver enzymes ~5%, Family history ~5–8%
- Younger/healthier patients more likely to have missing labs

---

## Validation Process

### Per-Patient Validation
- ✓ Age within [18, 85], Gender is Male/Female
- ✓ BMI matches Weight/(Height/100)² within ±0.5
- ✓ SBP > DBP, both within valid ranges
- ✓ All features within specification bounds
- ✓ T2D=1 ⇒ FPG≥126 or HbA1c≥6.5
- ✓ Prediabetes=1 ⇒ FPG 100–125 or HbA1c 5.7–6.4 (and NOT T2D)
- ✓ Obesity=1 ⇒ BMI≥30
- ✓ MetS=1 ⇒ ≥3 criteria met
- ✓ Healthy=1 ⇒ all diseases = 0

### Dataset-Wide Validation
- ✓ All Patient_IDs unique
- ✓ Disease prevalence within ±3% of targets
- ✓ Missing rates match specification
- ✓ Correlation signs correct (BMI↔Waist +, BMI↔HDL −, FPG↔HbA1c +)
- ✓ Mandatory features have no missing values
- ✓ Correct row and column counts

---

## Output Dataset Schema

| # | Feature | Type | Unit | Range | Missing % |
|---|---|---|---|---|---|
| 1 | Patient_ID | String | — | P00001–P20000 | 0% |
| 2 | Age | Integer | years | 18–85 | 0% |
| 3 | Gender | String | — | Male/Female | 0% |
| 4 | Height_cm | Float | cm | 140–200 | 0% |
| 5 | Weight_kg | Float | kg | 40–150 | 0% |
| 6 | BMI | Float | kg/m² | 16–45 | 0% |
| 7 | Waist_Circumference_cm | Float | cm | 60–140 | ~3% |
| 8 | Systolic_BP | Integer | mmHg | 90–190 | 0% |
| 9 | Diastolic_BP | Integer | mmHg | 60–120 | 0% |
| 10 | Fasting_Blood_Glucose | Integer | mg/dL | 70–250 | 0% |
| 11 | HbA1c | Float | % | 4.5–12.0 | 0% |
| 12 | LDL_Cholesterol | Integer | mg/dL | 40–250 | ~2% |
| 13 | HDL_Cholesterol | Integer | mg/dL | 20–90 | ~2% |
| 14 | Triglycerides | Integer | mg/dL | 40–500 | ~2% |
| 15 | ALT | Integer | U/L | 10–200 | ~5% |
| 16 | AST | Integer | U/L | 10–150 | ~5% |
| 17 | Family_History_Diabetes | Binary | — | 0/1 | ~5% |
| 18 | Family_History_Obesity | Binary | — | 0/1 | ~5% |
| 19 | Family_History_Hypertension | Binary | — | 0/1 | ~5% |
| 20 | Family_History_NAFLD | Binary | — | 0/1 | ~8% |
| 21 | Type2_Diabetes | Binary | — | 0/1 | 0% |
| 22 | Prediabetes | Binary | — | 0/1 | 0% |
| 23 | Obesity | Binary | — | 0/1 | 0% |
| 24 | Metabolic_Syndrome | Binary | — | 0/1 | 0% |
| 25 | NAFLD | Binary | — | 0/1 | 0% |
| 26 | Healthy | Binary | — | 0/1 | 0% |

---

## Configuration

All parameters are centralized in `config.py`. Key configurable values:

- **Dataset size** and **random seed**
- **Age/gender distributions**
- **BMI category proportions**
- **Disease prevalence targets**
- **Noise magnitudes**
- **Missing value percentages**
- **Clinical diagnostic thresholds**
- **Feature correlation parameters**

---

## ML Readiness

The generated dataset is ready for machine learning:
- All features are numeric (Gender encoded as string for flexibility)
- Disease labels are binary (0/1)
- Missing values represented as NaN (compatible with pandas/sklearn imputation)
- No label leakage (features generated before labels)
- Balanced enough for tree-based models (Random Forest, XGBoost, LightGBM, CatBoost)
- Stratified splitting recommended for cross-validation

---

## References

- ADA Standards of Medical Care (diabetes/prediabetes criteria)
- WHO/CDC obesity definitions (BMI thresholds)
- ATP III/AHA/NHLBI Metabolic Syndrome criteria
- CDC cholesterol and triglyceride guidelines
- Mayo Clinic ALT/AST normal ranges
- AASLD NAFLD definition and risk factors
