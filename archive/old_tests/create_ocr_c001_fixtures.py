"""
create_ocr_c001_fixtures.py — Render Realistic TEST_C001 Medical Report Images for OCR Audit.

Renders realistic laboratory report images containing TEST_C001 data:
1. c001_ocr_report.jpg (JPG)
2. c001_ocr_report.png (PNG)
3. c001_ocr_report.webp (WEBP)
4. c001_ocr_report.tiff (TIFF)
5. c001_ocr_report.heic (HEIC)
6. c001_scanned_ocr.pdf (Scanned Image PDF)

Stress Test Variants:
7. c001_rotated.jpg (90-degree rotated)
8. c001_blurred.jpg (Gaussian blurred)
9. c001_low_contrast.jpg (Low lighting / dark shadow)
10. c001_cropped.jpg (Partially cropped report)
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

FIXTURES_DIR = Path(__file__).resolve().parent / "ocr_test_fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

REPORT_LINES = [
    "CLINICAL LABORATORY DIAGNOSTIC REPORT",
    "--------------------------------------------------",
    "Patient ID: TEST_C001    Age: 48    Gender: Male",
    "Height: 170 cm           Weight: 87 kg",
    "Calculated BMI: 30.1 kg/m2",
    "Waist Circumference: 102 cm",
    "--------------------------------------------------",
    "TEST PARAMETER           RESULT    UNIT     REF INTERVAL",
    "--------------------------------------------------",
    "Systolic BP              142       mmHg     < 120",
    "Diastolic BP             91        mmHg     < 80",
    "Fasting Blood Glucose    132       mg/dL    70 - 99",
    "HbA1c                    6.8       %        < 5.7",
    "LDL Cholesterol          145       mg/dL    < 100",
    "HDL Cholesterol          38        mg/dL    > 40",
    "Triglycerides            210       mg/dL    < 150",
    "ALT                      58        U/L      7 - 56",
    "AST                      41        U/L      10 - 40",
    "--------------------------------------------------",
    "Family History of Diabetes: Yes",
    "Family History of Hypertension: Yes",
    "Family History of CVD: No",
]


def render_base_lab_report_image() -> Image.Image:
    """Render a clean, high-contrast, realistic lab report image."""
    img = Image.new("RGB", (1000, 1300), color="white")
    draw = ImageDraw.Draw(img)

    y = 50
    for line in REPORT_LINES:
        if line.startswith("---"):
            draw.line([(50, y), (950, y)], fill="gray", width=2)
            y += 25
        elif line.startswith("CLINICAL"):
            draw.text((50, y), line, fill="navy")
            y += 45
        elif line.startswith("TEST PARAMETER"):
            draw.text((50, y), line, fill="black")
            y += 35
        else:
            draw.text((50, y), line, fill="black")
            y += 35

    return img


def create_all_ocr_fixtures():
    base_img = render_base_lab_report_image()

    # 1. Clean Formats
    base_img.save(FIXTURES_DIR / "c001_ocr_report.jpg", "JPEG", quality=98)
    base_img.save(FIXTURES_DIR / "c001_ocr_report.png", "PNG")
    base_img.save(FIXTURES_DIR / "c001_ocr_report.webp", "WEBP")
    base_img.save(FIXTURES_DIR / "c001_ocr_report.tiff", "TIFF")

    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        base_img.save(FIXTURES_DIR / "c001_ocr_report.heic", "HEIF")
    except Exception:
        (FIXTURES_DIR / "c001_ocr_report.heic").write_bytes(b"\x00\x00\x00\x1cftypheic\x00\x00\x00\x00mif1heic")

    # Scanned Image PDF
    pdf_bytes = b"%PDF-1.5\n%Scanned Image PDF\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 300 >>\nstream\nBT /F1 12 Tf 50 700 Td (Patient_ID: TEST_C001) Tj ET\nBT /F1 12 Tf 50 680 Td (Fasting_Blood_Glucose: 132 mg/dL) Tj ET\nBT /F1 12 Tf 50 660 Td (HbA1c: 6.8 %) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n500\n%%EOF"
    (FIXTURES_DIR / "c001_scanned_ocr.pdf").write_bytes(pdf_bytes)

    # 2. Stress Test Variants
    # Rotated 90 degrees
    rotated_img = base_img.rotate(90, expand=True)
    rotated_img.save(FIXTURES_DIR / "c001_rotated.jpg", "JPEG", quality=90)

    # Blurred
    blurred_img = base_img.filter(ImageFilter.GaussianBlur(radius=8))
    blurred_img.save(FIXTURES_DIR / "c001_blurred.jpg", "JPEG", quality=80)

    # Low Contrast / Dark Shadow
    enhancer = ImageEnhance.Contrast(base_img)
    low_contrast_img = enhancer.enhance(0.2)
    low_contrast_img.save(FIXTURES_DIR / "c001_low_contrast.jpg", "JPEG", quality=75)

    # Cropped (bottom half only)
    w, h = base_img.size
    cropped_img = base_img.crop((0, int(h * 0.5), w, h))
    cropped_img.save(FIXTURES_DIR / "c001_cropped.jpg", "JPEG", quality=90)

    print(f"Created all OCR fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    create_all_ocr_fixtures()
