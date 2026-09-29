"""
create_manifest_hashes.py — Computes SHA-256 hashes for frozen v3 datasets and model artifacts.
"""

import hashlib
import json
from pathlib import Path

DATA_DIR = Path("data/multimodal_v3")
MODEL_DIR = Path("expert_models/saved_models")

v3_files = [
    DATA_DIR / "clinical_v3.csv",
    DATA_DIR / "wearable_standard_v3.csv",
    DATA_DIR / "wearable_cgm_v3.csv",
    DATA_DIR / "gut_v3.csv",
    DATA_DIR / "labels_v3.csv",
    DATA_DIR / "split_manifest_v3.csv",
    MODEL_DIR / "clinical_v3" / "clinical_v3_payload.joblib",
    MODEL_DIR / "clinical_v3" / "clinical_v3_metrics.json",
    MODEL_DIR / "wearable_v3" / "wearable_v3_payload.joblib",
    MODEL_DIR / "wearable_v3" / "wearable_v3_metrics.json",
    MODEL_DIR / "gut_v3" / "gut_v3_payload.joblib",
    MODEL_DIR / "gut_v3" / "gut_v3_metrics.json",
    MODEL_DIR / "fusion_v3" / "fusion_v3_metrics.json",
    MODEL_DIR / "fusion_v3" / "wg_logistic_regression_stacker.joblib"
]

hashes = {}
for p in v3_files:
    if p.exists():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        hashes[str(p).replace("\\", "/")] = {
            "sha256": h.hexdigest(),
            "size_bytes": p.stat().st_size
        }

with open("v3_frozen_baseline_manifest.json", "w") as f:
    json.dump(hashes, f, indent=2)

print("Computed SHA-256 hashes for all frozen v3 artifacts:")
for k, v in hashes.items():
    print(f"  {k}: {v['sha256']} ({v['size_bytes']} bytes)")
