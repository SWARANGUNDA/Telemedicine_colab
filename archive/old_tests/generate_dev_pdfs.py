import base64
from pathlib import Path

p_gut = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_gut_microbiome.pdf")
p_wear = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_wearable.pdf")
p_clin = Path("TeleMed_5_Patient_Sets_15_PDFs/P_TEST_101_clinical.pdf")

g_b64 = base64.b64encode(p_gut.read_bytes()).decode()
w_b64 = base64.b64encode(p_wear.read_bytes()).decode()
c_b64 = base64.b64encode(p_clin.read_bytes()).decode()

out = f"""// Real PDF Base64 strings for Dev/Browser intake testing
export const GUT_PDF_B64 = "{g_b64}";
export const WEAR_PDF_B64 = "{w_b64}";
export const CLIN_PDF_B64 = "{c_b64}";

export function b64ToFile(b64Data, filename) {{
  const bytes = atob(b64Data);
  const arr = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
  const blob = new Blob([arr], {{ type: 'application/pdf' }});
  return new File([blob], filename, {{ type: 'application/pdf' }});
}}
"""

out_path = Path("web_platform/frontend/src/dev_pdfs.js")
out_path.write_text(out, encoding="utf-8")
print(f"Generated {out_path} successfully!")
