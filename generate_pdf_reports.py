import os
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import datetime

# Distinctly Telugu Names
telugu_first_names = [
    "Venkata", "Sai", "Krishna", "Rama", "Lakshmi", "Srinivasa", 
    "Suresh", "Ramesh", "Mahesh", "Bhavani", "Swati", "Anusha", 
    "Karthik", "Vamshi", "Ramakrishna", "Pavan", "Teja", "Kavya", "Sindhu"
]
telugu_surnames = [
    "Yarlagadda", "Nandamuri", "Akkineni", "Daggubati", "Konda", 
    "Pothineni", "Ghattamaneni", "Allu", "Konidela", "Uppalapati",
    "Golla", "Bokka", "Mekala", "Gaddam", "Dasari"
]

gut_taxa = [
    "Akkermansia muciniphila", "Faecalibacterium prausnitzii", "Roseburia intestinalis",
    "Bifidobacterium longum", "Bacteroides thetaiotaomicron", "Prevotella copri",
    "Ruminococcus bromii", "Blautia wexlerae", "Escherichia coli", "Lactobacillus acidophilus"
]

def generate_patient_data(profile_type):
    if profile_type == "Healthy_Young":
        age = random.randint(20, 35)
        weight = random.randint(55, 75)
        sys_bp, dia_bp = random.randint(110, 120), random.randint(70, 80)
        fbg = random.randint(80, 95)
        hba1c = round(random.uniform(4.5, 5.4), 1)
        steps = random.randint(8000, 14000)
    elif profile_type == "Diabetic_Elderly":
        age = random.randint(60, 80)
        weight = random.randint(75, 100)
        sys_bp, dia_bp = random.randint(135, 160), random.randint(85, 95)
        fbg = random.randint(126, 180)
        hba1c = round(random.uniform(6.5, 9.0), 1)
        steps = random.randint(2000, 5000)
    elif profile_type == "Athlete":
        age = random.randint(22, 40)
        weight = random.randint(65, 85)
        sys_bp, dia_bp = random.randint(100, 115), random.randint(60, 75)
        fbg = random.randint(75, 90)
        hba1c = round(random.uniform(4.5, 5.2), 1)
        steps = random.randint(12000, 20000)
    else: # Prediabetic_MiddleAged
        age = random.randint(40, 55)
        weight = random.randint(70, 95)
        sys_bp, dia_bp = random.randint(120, 135), random.randint(80, 85)
        fbg = random.randint(100, 125)
        hba1c = round(random.uniform(5.7, 6.4), 1)
        steps = random.randint(4000, 8000)

    gender = random.choice(["Male", "Female"])
    height = random.randint(155, 185)
    bmi = round(weight / ((height/100)**2), 1)
    
    return {
        "Clinical": {
            "Age": age, "Gender": gender, "Height (cm)": height, "Weight (kg)": weight, "BMI": bmi,
            "Waist Circumference (cm)": random.randint(75, 110),
            "Systolic BP (mmHg)": sys_bp, "Diastolic BP (mmHg)": dia_bp,
            "Fasting Blood Glucose (mg/dL)": fbg, "HbA1c (%)": hba1c,
            "Triglycerides (mg/dL)": random.randint(90, 250),
            "HDL (mg/dL)": random.randint(35, 65), "LDL (mg/dL)": random.randint(90, 160),
            "ALT (U/L)": random.randint(15, 60), "AST (U/L)": random.randint(15, 50)
        },
        "Wearable": {
            "Average Daily Steps": steps,
            "Active Minutes/Day": random.randint(10, 60),
            "Sedentary Time (min/day)": random.randint(300, 700),
            "Resting Heart Rate (bpm)": random.randint(55, 85),
            "HRV RMSSD (ms)": random.randint(20, 70),
            "Sleep Duration (hours)": round(random.uniform(5.0, 8.5), 1),
            "Sleep Efficiency Score": random.randint(65, 95),
            "Autonomic Stress Score": random.randint(30, 80),
            "Activity Energy Expenditure (kcal)": random.randint(200, 800),
            "Exercise Frequency (Days/Week)": random.randint(0, 5),
            "CGM Average Glucose (mg/dL)": random.randint(95, 140),
            "CGM Glucose CV (%)": random.randint(10, 30),
            "CGM Time In Range (%)": random.randint(50, 95),
            "CGM Time Above Range (%)": random.randint(5, 40),
            "CGM Time Below Range (%)": random.randint(0, 10)
        },
        "Gut Microbiome": {taxa: round(random.uniform(0.1, 15.0), 2) for taxa in gut_taxa},
        "_dob": datetime.date.today() - datetime.timedelta(days=age*365)
    }

def create_single_modality_pdf(filename, patient_name, data, modality_name, modality_data, headers, report_type_label):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=20, textColor=colors.HexColor('#1E3A8A'))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], spaceAfter=10, textColor=colors.HexColor('#0F172A'))
    elements = []
    
    elements.append(Paragraph("<b>TeleMed Central Diagnostic Laboratory</b>", title_style))
    elements.append(Paragraph("123 Health Avenue, Medical District, NY 10001 | Phone: 1-800-TELEMED", ParagraphStyle('Address', alignment=1, fontSize=10, textColor=colors.gray, spaceAfter=20)))
    
    patient_info = [
        ["Patient Name:", patient_name, "Report Date:", datetime.date.today().strftime('%B %d, %Y')],
        ["DOB:", data["_dob"].strftime('%B %d, %Y'), "Accession No:", f"TM-{random.randint(10000,99999)}"],
        ["Provider:", "Dr. TeleMed AI System", "Test Panel:", report_type_label]
    ]
    
    t_info = Table(patient_info, colWidths=[90, 150, 90, 150])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 25))
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3A8A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ])

    elements.append(Paragraph(f"<b>{modality_name}</b>", subtitle_style))
    table_data = [headers]
    for key, val in modality_data.items():
        if key != "_dob":
            table_data.append([key, str(val)])
    t = Table(table_data, colWidths=[250, 200])
    t.setStyle(table_style)
    elements.append(t)
    elements.append(Spacer(1, 20))

    disclaimer = "CLINICAL DISCLAIMER: This document is a simulated synthetic medical report intended for system testing and validation only. The metrics presented do not belong to a real patient and should not be used for diagnosis."
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"<i>{disclaimer}</i>", ParagraphStyle('Disclaimer', fontSize=8, textColor=colors.gray, alignment=1)))

    doc.build(elements)

os.makedirs("test_reports/separated_pdf_reports", exist_ok=True)
profiles = ["Healthy_Young", "Diabetic_Elderly", "Athlete", "Prediabetic_MiddleAged"]

print("Generating 20 patients x 3 separated PDF reports...")
for i in range(1, 21):
    first_name = random.choice(telugu_first_names)
    last_name = random.choice(telugu_surnames)
    full_name = f"{first_name} {last_name}"
    
    profile = profiles[i % 4] 
    data = generate_patient_data(profile)
    
    # 1. Clinical PDF
    clinical_file = f"test_reports/separated_pdf_reports/P{i}_{first_name}_Clinical.pdf"
    create_single_modality_pdf(clinical_file, full_name, data, "Clinical Laboratory Panel", data["Clinical"], ["Biomarker", "Measured Value"], "Isolated Clinical Profile")
    
    # 2. Wearable PDF
    wearable_file = f"test_reports/separated_pdf_reports/P{i}_{first_name}_Wearable.pdf"
    create_single_modality_pdf(wearable_file, full_name, data, "Wearable Telemetry & CGM (30-Day Average)", data["Wearable"], ["Metric", "Aggregated Value"], "Isolated Wearable Profile")
    
    # 3. Gut PDF
    gut_file = f"test_reports/separated_pdf_reports/P{i}_{first_name}_Gut.pdf"
    create_single_modality_pdf(gut_file, full_name, data, "Gut Microbiome Composition", data["Gut Microbiome"], ["Bacterial Taxa", "Relative Abundance (%)"], "Isolated Gut Microbiome Profile")
    
    print(f"[{i}/20] Generated separated reports for {full_name}")

print("Successfully generated all separated PDF reports!")
