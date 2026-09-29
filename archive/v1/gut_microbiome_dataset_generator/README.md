# Gut Microbiome Dataset Generator

## Overview

A production-quality Python package that generates a synthetic **Gut Microbiome Dataset** for a multimodal healthcare AI system. The dataset simulates clinical 16S rRNA sequencing reports for 20,000 synthetic patients, aligned with the Master Clinical Dataset.

This is part of the **"Generative AI Assisted Telemedicine Platform for Personalized Gut Microbiome Analysis"** project, which predicts five metabolic diseases:

- **Type 2 Diabetes**
- **Prediabetes**
- **Obesity**
- **Metabolic Syndrome**
- **Non-Alcoholic Fatty Liver Disease (NAFLD)**

## System Architecture

```
Clinical Dataset         Wearable Dataset         Gut Microbiome Dataset
      ↓                       ↓                          ↓
Clinical Expert Model    Wearable Expert Model    Gut Expert Model
      ↓                       ↓                          ↓
                    ┌─────────────────────┐
                    │    Fusion Engine    │
                    └─────────────────────┘
                              ↓
                    Final Disease Prediction
```

## Generated Features

| # | Feature                  | Type                   | Range       |
|---|--------------------------|------------------------|-------------|
| 1 | Akkermansia              | Relative Abundance (%) | 0 – 25%     |
| 2 | Faecalibacterium         | Relative Abundance (%) | 0 – 35%     |
| 3 | Bifidobacterium          | Relative Abundance (%) | 0 – 20%     |
| 4 | Escherichia_Shigella     | Relative Abundance (%) | 0 – 20%     |
| 5 | Roseburia                | Relative Abundance (%) | 0 – 18%     |
| 6 | Blautia                  | Relative Abundance (%) | 0 – 20%     |
| 7 | Prevotella               | Relative Abundance (%) | 0 – 30%     |
| 8 | Collinsella              | Relative Abundance (%) | 0 – 15%     |
| 9 | Alistipes                | Relative Abundance (%) | 0 – 15%     |
| 10| Shannon_Diversity_Index  | Alpha-diversity score  | 1.0 – 5.0   |

## Scientific Rationale

Features were selected based on 2020–2025 systematic reviews and meta-analyses:

- **Beneficial bacteria** (Akkermansia, Faecalibacterium, Bifidobacterium, Roseburia, Alistipes): Depleted in metabolic disease; produce SCFAs; maintain gut barrier integrity.
- **Inflammatory bacteria** (Escherichia/Shigella, Collinsella): Elevated in T2D, obesity, NAFLD; produce LPS and pro-inflammatory compounds.
- **Context-dependent bacteria** (Prevotella, Blautia): Variable across populations; diet and geography dependent.
- **Shannon Diversity Index**: Community-level dysbiosis marker.

## Multimodal Alignment

The dataset maintains exact alignment with `Clinical_Dataset.csv`:

| Column              | Source            |
|---------------------|-------------------|
| Patient_ID          | Copied exactly    |
| Age                 | Copied exactly    |
| Gender              | Copied exactly    |
| Type2_Diabetes      | Copied exactly    |
| Prediabetes         | Copied exactly    |
| Obesity             | Copied exactly    |
| Metabolic_Syndrome  | Copied exactly    |
| NAFLD               | Copied exactly    |
| Healthy             | Copied exactly    |

Disease labels are alignment metadata only — **NOT** predictor variables for the Gut Expert Model.

## Generation Pipeline

1. Load `Clinical_Dataset.csv`
2. Compute latent metabolic risk scores from clinical biomarkers
3. Compute disease-specific abundance shift factors
4. Generate beneficial bacteria (truncated normal distributions)
5. Generate inflammatory bacteria (gamma distributions)
6. Generate context-dependent bacteria (log-normal distributions)
7. Apply Gaussian Copula correlation structure
8. Generate Shannon Diversity Index
9. Inject biological noise
10. Validate every patient (regenerate failures)
11. Validate complete dataset
12. Export all output files

## Usage

```bash
# Install dependencies
pip install -r gut_microbiome_dataset_generator/requirements.txt

# Run the generator
python -m gut_microbiome_dataset_generator.main --clinical-path Clinical_Dataset.csv

# With custom options
python -m gut_microbiome_dataset_generator.main \
    --clinical-path Clinical_Dataset.csv \
    --output-dir ./output \
    --seed 42 \
    --noise-scale 1.0 \
    --correlation-strength 0.8
```

## Output Files

| File                            | Description                                    |
|---------------------------------|------------------------------------------------|
| `Gut_Microbiome_Dataset.csv`    | Final 20,000-patient dataset                   |
| `dataset_summary.csv`           | Summary statistics for all features             |
| `feature_distribution_report.txt` | Detailed distribution analysis                |
| `correlation_matrix.csv`        | Pairwise feature correlation matrix             |
| `validation_report.txt`         | Comprehensive validation results                |

## Project Structure

```
gut_microbiome_dataset_generator/
├── __init__.py          # Package metadata
├── config.py            # Configuration dataclass
├── constants.py         # Biological bounds, distributions, correlations
├── loader.py            # Clinical Dataset loader
├── distributions.py     # Statistical distribution samplers
├── disease_profile.py   # Metabolic risk score computation
├── bacteria.py          # Bacterial abundance generators
├── diversity.py         # Shannon Diversity Index modeler
├── correlations.py      # Gaussian Copula correlation engine
├── noise.py             # Biological noise injection
├── validation.py        # Patient and dataset validators
├── exporter.py          # Output file exporters
├── generator.py         # Core orchestration pipeline
├── main.py              # CLI entry point
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Requirements

- Python 3.11+
- NumPy ≥ 1.24
- Pandas ≥ 2.0
- SciPy ≥ 1.10

## Reproducibility

The generator uses `numpy.random.default_rng(seed)` for full deterministic reproducibility. Default seed: 42.
