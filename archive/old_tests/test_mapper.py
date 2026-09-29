from services.multimodal_intake.extractor import extract_key_value_pairs_from_text
from services.multimodal_intake.mapper import map_extracted_features
import pypdf
from pathlib import Path

p_gut = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
p_wear = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")

reader_g = pypdf.PdfReader(str(p_gut))
text_g = "\n".join(p.extract_text() or "" for p in reader_g.pages)
pairs_g = extract_key_value_pairs_from_text(text_g, p_gut.name)
mapped_g = map_extracted_features(pairs_g)

print("=== MAPPED GUT ===")
print("CLINICAL:", mapped_g.get("CLINICAL"))
print("WEARABLE:", mapped_g.get("WEARABLE"))
print("GUT_MICROBIOME:", mapped_g.get("GUT_MICROBIOME"))

reader_w = pypdf.PdfReader(str(p_wear))
text_w = "\n".join(p.extract_text() or "" for p in reader_w.pages)
pairs_w = extract_key_value_pairs_from_text(text_w, p_wear.name)
mapped_w = map_extracted_features(pairs_w)

print("\n=== MAPPED WEARABLE ===")
print("CLINICAL:", mapped_w.get("CLINICAL"))
print("WEARABLE:", mapped_w.get("WEARABLE"))
print("GUT_MICROBIOME:", mapped_w.get("GUT_MICROBIOME"))
