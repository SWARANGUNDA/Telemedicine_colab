from pathlib import Path
from services.multimodal_intake.extractor import extract_from_pdf_bytes, extract_key_value_pairs_from_text
import pypdf

p_gut = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
p_wear = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")

print("=== GUT PDF TEXT ===")
reader_g = pypdf.PdfReader(str(p_gut))
text_g = "\n".join(p.extract_text() or "" for p in reader_g.pages)
print(text_g)
print("\n--- GUT EXTRACTED PAIRS ---")
pairs_g = extract_key_value_pairs_from_text(text_g, p_gut.name)
for k, v in pairs_g.items():
    print(f"  {k} -> {v.get('raw_value')}")

print("\n=== WEARABLE PDF TEXT ===")
reader_w = pypdf.PdfReader(str(p_wear))
text_w = "\n".join(p.extract_text() or "" for p in reader_w.pages)
print(text_w)
print("\n--- WEARABLE EXTRACTED PAIRS ---")
pairs_w = extract_key_value_pairs_from_text(text_w, p_wear.name)
for k, v in pairs_w.items():
    print(f"  {k} -> {v.get('raw_value')}")
