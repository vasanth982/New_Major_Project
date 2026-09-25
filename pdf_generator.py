"""
Clinical PDF Report Generator for Checkup Buddy (v2).
Constructs hospital-grade, multi-page diagnostic PDF reports using fpdf2,
featuring clinical letterhead, bordered vitals table, diagnostic risk badges,
specific test inputs table, tailored physician questions, and regulatory disclaimers.
Fully internationalized with support for 13 pan-India languages.
"""

import os
from datetime import datetime
from fpdf import FPDF
import i18n

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images", "Logo 1.png")


def sanitize_text(text: str) -> str:
    """Replaces non-latin1 unicode symbols with clean ASCII equivalents when rendering standard fonts."""
    if not text:
        return ""
    replacements = {
        "°": " deg ",
        "≥": ">=",
        "≤": "<=",
        "•": "-",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "μ": "u",
        "²": "2",
        "³": "3",
        "✓": "[OK]",
        "✗": "[X]",
        "❤️": "",
        "🩸": "",
        "🧠": "",
        "🧪": "",
        "🧬": "",
        "🎗️": "",
        "💡": "",
        "⚠️": "WARNING: ",
        "🥗": "",
        "🚨": "ALERT: ",
        "👨‍⚕️": "",
        "⚖️": "",
        "📄": "",
        "🛡️": ""
    }
    cleaned = str(text)
    for k, v in replacements.items():
        cleaned = cleaned.replace(k, v)
    return cleaned.encode("latin-1", "replace").decode("latin-1")


class ClinicalReportPDF(FPDF):
    def __init__(self, patient_code: str, report_time: str, trans: dict, font_family: str = "helvetica"):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.patient_code = patient_code
        self.report_time = report_time
        self.trans = trans
        self.font_family = font_family
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Top letterhead border bar
        self.set_fill_color(13, 148, 136)  # Serene Teal
        self.rect(0, 0, 210, 5, "F")

        # Logo
        if os.path.exists(LOGO_PATH):
            try:
                self.image(LOGO_PATH, x=14, y=9, w=18)
            except Exception:
                pass

        # Clinic Header Information
        self.set_xy(36, 9)
        self.set_font(self.font_family, "B" if self.font_family == "helvetica" else "", 14)
        self.set_text_color(15, 23, 42)
        h_title = self.trans.get("pdf_header_title", "CHECKUP BUDDY HEALTH ANALYTICS")
        self.cell(0, 6, h_title if self.font_family != "helvetica" else sanitize_text(h_title), ln=True)

        self.set_xy(36, 15)
        self.set_font(self.font_family, "", 8)
        self.set_text_color(100, 116, 139)
        h_sub = self.trans.get("pdf_header_subtitle", "Preventive Diagnostics & Multi-Disease Machine Learning Laboratory")
        self.cell(0, 4, h_sub if self.font_family != "helvetica" else sanitize_text(h_sub), ln=True)

        self.set_xy(36, 19)
        self.set_font(self.font_family, "" if self.font_family != "helvetica" else "I", 7.5)
        conf_lbl = self.trans.get("pdf_confidential", "Confidential Medical Record")
        self.cell(0, 4, f"Report ID: {self.patient_code}  |  Generated: {self.report_time}  |  {conf_lbl}", ln=True)

        # Decorative dividing line
        self.set_draw_color(203, 213, 225)
        self.set_line_width(0.4)
        self.line(14, 26, 196, 26)
        self.ln(6)

    def footer(self):
        self.set_y(-16)
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.3)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(1.5)

        self.set_font(self.font_family, "", 7)
        self.set_text_color(148, 163, 184)
        disclaimer = self.trans.get("pdf_disclaimer", "DISCLAIMER: Educational and preventive screening tool only.")
        clean_disclaimer = disclaimer if self.font_family != "helvetica" else sanitize_text(disclaimer)
        self.cell(150, 4, clean_disclaimer[:130], align="L")
        self.cell(32, 4, f"Page {self.page_no()}/{{nb}}", align="R")


def generate_clinical_pdf(
    patient_name: str,
    patient_id: int,
    age: int,
    gender: str,
    vitals: dict,
    disease_name: str,
    result_title: str,
    risk_level: str,
    confidence_pct: float,
    inputs_dict: dict,
    recommendation: dict,
    lang: str = None
) -> bytes:
    """
    Constructs a complete clinical diagnostic report as PDF bytes in the active language.
    """
    if lang is None:
        lang = i18n.get_current_language()

    trans = i18n.load_translations(lang)
    patient_code = f"CB-{patient_id:06d}"
    report_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Font setup: If non-english, detect and load Unicode Indic TTF
    font_family = "helvetica"
    windows_font = r"C:\Windows\Fonts\Nirmala.ttc"
    use_unicode = False

    if lang != "en" and os.path.exists(windows_font):
        font_family = "Nirmala"
        use_unicode = True

    pdf = ClinicalReportPDF(patient_code=patient_code, report_time=report_time, trans=trans, font_family=font_family)
    
    if use_unicode:
        try:
            pdf.add_font("Nirmala", fname=windows_font)
        except Exception:
            pdf.font_family = "helvetica"
            font_family = "helvetica"

    def t_text(txt: str) -> str:
        if font_family == "helvetica":
            return sanitize_text(txt)
        return str(txt)

    pdf.alias_nb_pages()
    pdf.add_page()

    # 1. Patient Demographics Block
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    pdf.rect(14, 29, 182, 22, "DF")

    pdf.set_xy(18, 31)
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(50, 5, t_text(trans.get("pdf_patient_info", "PATIENT INFORMATION")))
    pdf.set_font(font_family, "", 8.5)
    pdf.set_text_color(15, 23, 42)

    lbl_name = trans.get("pdf_name", "Name")
    lbl_age = trans.get("pdf_age", "Age")
    lbl_gender = trans.get("pdf_gender", "Gender")
    lbl_mrn = trans.get("pdf_mrn", "MRN")
    lbl_session = trans.get("pdf_session_id", "Session ID")
    lbl_date = trans.get("pdf_date", "Date")

    pdf.set_xy(18, 37)
    pdf.cell(60, 5, t_text(f"{lbl_name}: {patient_name}"))
    pdf.cell(40, 5, t_text(f"{lbl_age}: {age}"))
    pdf.cell(40, 5, t_text(f"{lbl_gender}: {gender}"))
    pdf.cell(40, 5, t_text(f"{lbl_mrn}: {patient_code}"))

    pdf.set_xy(18, 43)
    pdf.cell(60, 5, t_text(f"{lbl_session}: #{vitals.get('session_id', 'N/A')}"))
    pdf.cell(60, 5, t_text("Referral: Self-Service Preventive Portal"))
    pdf.cell(60, 5, t_text(f"{lbl_date}: {report_time.split()[0]}"))

    pdf.set_y(54)

    # 2. Bordered Baseline Vitals Intake Table
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, t_text(trans.get("pdf_vitals_header", "1. MANDATORY CLINICAL VITALS INTAKE")), ln=True)

    # Table Header
    pdf.set_fill_color(241, 245, 249)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 8)
    pdf.set_text_color(51, 65, 85)

    col_widths = [45, 45, 50, 42]
    pdf.cell(col_widths[0], 6, t_text(trans.get("pdf_metric", "Physiological Metric")), border=1, fill=True)
    pdf.cell(col_widths[1], 6, t_text(trans.get("pdf_recorded", "Recorded Value")), border=1, fill=True)
    pdf.cell(col_widths[2], 6, t_text(trans.get("pdf_range", "Standard Clinical Range")), border=1, fill=True)
    pdf.cell(col_widths[3], 6, t_text(trans.get("pdf_status", "Status Evaluation")), border=1, ln=True, fill=True)

    # Table Rows
    pdf.set_font(font_family, "", 8)
    pdf.set_text_color(15, 23, 42)

    v_temp = vitals.get("body_temp", 37.0)
    v_sys = vitals.get("blood_pressure_sys", 120)
    v_dia = vitals.get("blood_pressure_dia", 80)
    v_sugar = vitals.get("blood_sugar", 95.0)
    v_bmi = vitals.get("bmi")
    v_bmi_str = f"{v_bmi:.1f} kg/m2" if v_bmi else "Not calculated"

    rows = [
        (trans.get("field_temp", "Body Temperature"), f"{v_temp:.1f} °C", "36.5 - 37.5 °C", "Normal" if 36.0 <= v_temp <= 37.5 else "Elevated"),
        (trans.get("field_bp_sys", "Blood Pressure"), f"{v_sys} / {v_dia} mmHg", "90-120 / 60-80 mmHg", "Optimal" if v_sys < 120 and v_dia < 80 else "Elevated"),
        (trans.get("field_blood_sugar", "Blood Glucose"), f"{v_sugar:.1f} mg/dL", "70.0 - 99.0 mg/dL", "Normal" if v_sugar < 100 else "Impaired"),
        (trans.get("field_bmi", "Body Mass Index"), v_bmi_str, "18.5 - 24.9 kg/m2", "Normal" if (v_bmi and 18.5 <= v_bmi < 25) else "Elevated")
    ]

    for label, val, rng, stat in rows:
        pdf.cell(col_widths[0], 5.5, t_text(label), border=1)
        pdf.cell(col_widths[1], 5.5, t_text(val), border=1)
        pdf.cell(col_widths[2], 5.5, t_text(rng), border=1)
        pdf.cell(col_widths[3], 5.5, t_text(stat), border=1, ln=True)

    pdf.ln(5)

    # 3. Diagnostic Assessment & Colored Result Badge
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 10)
    pdf.set_text_color(15, 23, 42)
    res_header_prefix = trans.get("pdf_result_header", "2. DIAGNOSTIC RESULT")
    pdf.cell(0, 6, t_text(f"{res_header_prefix}: {disease_name.upper()}"), ln=True)

    is_high_risk = "High" in risk_level or "Detected" in risk_level
    box_bg = (254, 242, 242) if is_high_risk else (240, 253, 244)
    box_border = (239, 68, 68) if is_high_risk else (34, 197, 94)
    text_color = (185, 28, 28) if is_high_risk else (21, 128, 61)

    cur_y = pdf.get_y()
    pdf.set_fill_color(*box_bg)
    pdf.set_draw_color(*box_border)
    pdf.set_line_width(0.5)
    pdf.rect(14, cur_y, 182, 16, "DF")

    pdf.set_xy(18, cur_y + 3)
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 10.5)
    pdf.set_text_color(*text_color)
    pdf.cell(110, 5, t_text(result_title))

    pdf.set_xy(135, cur_y + 3)
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 9)
    badge_label = f"[{risk_level.upper()} - {confidence_pct:.1f}%]"
    pdf.cell(57, 5, t_text(badge_label), align="R")

    pdf.set_xy(18, cur_y + 9)
    pdf.set_font(font_family, "", 8)
    pdf.set_text_color(51, 65, 85)
    summary_text = recommendation.get("summary", "")
    pdf.cell(170, 4, t_text(summary_text))

    pdf.set_y(cur_y + 20)

    # 4. Clinical Input Parameters Table
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 9)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, t_text(trans.get("pdf_inputs_header", "Diagnostic Inputs Evaluated:")), ln=True)

    pdf.set_font(font_family, "", 7.5)
    pdf.set_text_color(30, 41, 59)
    col_w_param = 91

    items = list(inputs_dict.items())
    for i in range(0, len(items), 2):
        k1, v1 = items[i]
        line1 = f" {k1}: {v1}"
        pdf.cell(col_w_param, 4.5, t_text(line1), border=1)

        if i + 1 < len(items):
            k2, v2 = items[i + 1]
            line2 = f" {k2}: {v2}"
            pdf.cell(col_w_param, 4.5, t_text(line2), border=1, ln=True)
        else:
            pdf.cell(col_w_param, 4.5, "", border=1, ln=True)

    pdf.ln(5)

    # 5. Recommendations Section
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, t_text(trans.get("pdf_recommendations_header", "3. CLINICAL RECOMMENDATIONS & ACTION PLAN")), ln=True)

    # Lifestyle
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 8.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, t_text(trans.get("pdf_lifestyle", "Lifestyle Modifications:")), ln=True)
    pdf.set_font(font_family, "", 8)
    pdf.set_text_color(51, 65, 85)
    for act in recommendation.get("lifestyle", [])[:4]:
        pdf.cell(5, 4, "-")
        pdf.multi_cell(175, 4, t_text(act))

    # Urgent Warning Signs
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 8.5)
    pdf.set_text_color(185, 28, 28)
    pdf.cell(0, 5, t_text(trans.get("pdf_urgent", "When to Seek Immediate Medical Attention:")), ln=True)
    pdf.set_font(font_family, "", 8)
    pdf.set_text_color(51, 65, 85)
    for sign in recommendation.get("urgent_signs", [])[:3]:
        pdf.cell(5, 4, "!")
        pdf.multi_cell(175, 4, t_text(sign))

    # Questions for Physician
    pdf.set_font(font_family, "B" if font_family == "helvetica" else "", 8.5)
    pdf.set_text_color(13, 148, 136)
    pdf.cell(0, 5, t_text(trans.get("pdf_questions", "Questions to Discuss with Your Attending Physician:")), ln=True)
    pdf.set_font(font_family, "" if font_family != "helvetica" else "I", 8)
    pdf.set_text_color(71, 85, 105)
    for q in recommendation.get("doctor_questions", [])[:3]:
        pdf.cell(5, 4, ">")
        pdf.multi_cell(175, 4, t_text(f'"{q}"'))

    return bytes(pdf.output())
