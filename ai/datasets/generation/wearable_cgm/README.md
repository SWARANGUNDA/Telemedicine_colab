# Wearable Dataset Generator (`wearable_dataset_generator`)

**Generative AI Assisted Telemedicine Platform — Synthetic Wearable EHR Dataset Generator**

A production-quality, research-grade Python package that generates medically realistic synthetic wearable device metrics (physical activity, continuous glucose monitoring [CGM], cardiovascular metrics, and sleep duration) conditioned on the Master Patient Dataset (`Clinical_Dataset.csv`).

---

## 📌 Research Context & Multimodal Architecture

This platform relies on three independent expert datasets and models:
1. **Clinical Dataset & Expert Model** (Master Patient Population)
2. **Wearable Dataset & Expert Model** (Conditioned on Master Patient Population)
3. **Gut Microbiome Dataset & Expert Model** (Conditioned on Master Patient Population)

The Wearable Dataset Generator **does not create an independent synthetic population**. Instead, it loads `Clinical_Dataset.csv` as the authoritative Master Patient Dataset, preserving every patient's identity (`Patient_ID`, `Age`, `Gender`) and target disease labels (`Type2_Diabetes`, `Prediabetes`, `Obesity`, `Metabolic_Syndrome`, `NAFLD`, `Healthy`). Wearable measurements are generated using stochastic physiological transfer functions conditioned on continuous clinical biomarkers ($BMI$, $FPG$, $HbA1c$, $BP$, $Lipids$).

```
Clinical_Dataset.csv (Master Population: P00001 - P20000)
       │
       ├── Preserves: Patient_ID, Age, Gender, Disease Labels
       └── Conditions: BMI, FPG, HbA1c, Blood Pressure, Lipids
               │
               ▼
   Wearable Dataset Generator (stochastic physiological transfer)
               │
               ▼
   Wearable_Dataset.csv (Matched 1-to-1 with Clinical_Dataset.csv)
```

---

## 📊 Features Schema

| # | Feature | Type | Unit | Range / Constraints | Description |
|---|---|---|---|---|---|
| 1 | `Patient_ID` | String | — | `P00001`–`P20000` | Preserved from `Clinical_Dataset.csv` |
| 2 | `Age` | Int | years | 18–80 | Preserved from `Clinical_Dataset.csv` |
| 3 | `Gender` | String | — | `Male`/`Female` | Preserved from `Clinical_Dataset.csv` |
| 4 | `Average_Daily_Steps` | Int | steps/day | 1,000–25,000 | Daily physical activity volume |
| 5 | `Active_Minutes` | Float | min/day | 0.0–180.0 | Moderate-to-vigorous activity (MVPA) |
| 6 | `Sedentary_Time_Minutes` | Float | min/day | 120.0–960.0 | Daily inactive time (5–16 hours) |
| 7 | `Resting_Heart_Rate` | Float | bpm | 40.0–100.0 | Awake resting heart rate |
| 8 | `Sleep_Duration` | Float | hours | 4.0–12.0 | Average nightly sleep time |
| 9 | `Calories_Burned` | Float | kcal/day | 800.0–4,000.0 | Daily energy expenditure estimate |
| 10 | `Average_Glucose` | Float | mg/dL | 60.0–250.0 | CGM continuous glucose mean |
| 11 | `Glucose_Variability` | Float | mg/dL | 5.0–50.0 | CGM standard deviation ($CV \approx 10\text{--}30\%$) |
| 12 | `Time_In_Range` | Float | % | 0.0–100.0 | CGM % time in 70–180 mg/dL |
| 13 | `Time_Above_Range` | Float | % | 0.0–100.0 | CGM % time $>180$ mg/dL ($TIR + TAR + TBR = 100\%$) |
| 14 | `Type2_Diabetes` | Binary | — | 0 / 1 | Preserved metadata target |
| 15 | `Prediabetes` | Binary | — | 0 / 1 | Preserved metadata target |
| 16 | `Obesity` | Binary | — | 0 / 1 | Preserved metadata target |
| 17 | `Metabolic_Syndrome` | Binary | — | 0 / 1 | Preserved metadata target |
| 18 | `NAFLD` | Binary | — | 0 / 1 | Preserved metadata target |
| 19 | `Healthy` | Binary | — | 0 / 1 | Preserved metadata target |

---

## 🛠️ Project Structure

```
wearable_dataset_generator/
├── __init__.py           # Package initialization
├── config.py              # Central configuration dataclass & parameters
├── constants.py           # Feature limits, column orders, medical constants
├── demographics.py       # Patient identity preservation & clinical loader
├── activity.py           # Activity feature generation (Steps, Active, Sedentary, Calories)
├── heart.py              # Cardiovascular feature generation (Resting Heart Rate)
├── sleep.py              # Sleep feature generation (Sleep Duration)
├── glucose.py            # Continuous Glucose Monitoring generation (CGM metrics)
├── correlations.py       # Inter-feature physiological dependency adjustments
├── validation.py         # Per-patient & dataset validation + regeneration loop
├── noise.py              # Gaussian measurement noise, MAR missingness, outlier injection
├── generator.py          # Complete generation pipeline orchestrator
├── utils.py              # Shared statistical functions & report generators
├── main.py               # CLI entrypoint & CSV exporter
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

---

## 🚀 Installation & Usage

### Prerequisites
- Python 3.11 or higher
- `Clinical_Dataset.csv` located in root directory

### Setup
```bash
pip install -r wearable_dataset_generator/requirements.txt
```

### Execution Options

```bash
# Demo Mode (100 patients for fast testing)
python -m wearable_dataset_generator.main --demo

# Full Generation (20,000 matched patients with seed 42)
python -m wearable_dataset_generator.main

# Custom Seed & Custom Master File
python -m wearable_dataset_generator.main --seed 123 --clinical-file Clinical_Dataset.csv
```

---

## 📜 Scientific References & Medical Guidelines

- **ADA Standards of Care (2023/2024)**: CGM consensus targets ($TIR \ge 70\%$ for 70–180 mg/dL, $TAR < 25\%$ for $>180$ mg/dL).
- **WHO Guidelines on Physical Activity (2020)**: $\ge 150$ min/week MVPA ($\approx 21$ min/day).
- **All of Us Wearables Study (Zheng et al., Nat. Commun. 2026)**: Step count offsets for sedentary time in obesity and T2D.
- **Inoue et al., Hypertens Res. (2009)**: Resting heart rate as a predictor of metabolic syndrome.
