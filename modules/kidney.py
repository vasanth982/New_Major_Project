"""
Chronic Kidney Disease (CKD) Assessment Module for Checkup Buddy (v2).
Pre-fills Age, Blood Pressure, and Blood Glucose from active vitals session.
Predicts renal risk using Random Forest and provides immediate clinical insights + PDF export.
"""

import streamlit as st
import os
import pickle
import numpy as np

import database
import recommendations
import pdf_generator
import diagnostic_helper

SAVED_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Saved_Models")


@st.cache_resource
def load_kidney_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "kidney_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "kidney_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_kidney_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                🧪 Chronic Kidney Disease (CKD) Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Evaluates renal filtration, urinalysis specific gravity/albumin, and serum biochemical markers.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    # Pre-fills from active vitals session
    vitals_age = vitals.get("age", 40)
    vitals_bp = vitals.get("blood_pressure_dia", 80)
    vitals_sugar = vitals.get("blood_sugar", 100.0)

    st.markdown("""
        <div style="background: #F1F5F9; border-left: 4px solid #3B82F6; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #334155;">
            <b>Intake Data Linked:</b> Age (<b>{}</b>), Blood Pressure (<b>{} mmHg</b>), Blood Glucose (<b>{} mg/dL</b>) have been pre-filled from your intake session.
        </div>
    """.format(vitals_age, vitals_bp, vitals_sugar), unsafe_allow_html=True)

    # ── X-ray / Renal Imaging Upload (Optional) ───────────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Chronic Kidney Disease", key_suffix="kidney", modality="X-ray / Ultrasound Scan")

    with st.form("kidney_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Age (Years)", value=str(vitals_age), disabled=True)
            st.text_input("Blood Pressure (bp) [mmHg]", value=str(vitals_bp), disabled=True)
            st.text_input("Blood Glucose Random (bgr) [mg/dL]", value=f"{vitals_sugar:.1f}", disabled=True)

            sg_options = [1.005, 1.010, 1.015, 1.020, 1.025]
            sg = st.selectbox("Urinary Specific Gravity (sg)", options=sg_options, index=3)
            al = st.selectbox("Urinary Albumin Grade (al)", options=[0, 1, 2, 3, 4, 5], index=0)

        with col2:
            su = st.selectbox("Urinary Sugar Grade (su)", options=[0, 1, 2, 3, 4, 5], index=0)
            bu = st.number_input("Blood Urea (bu) [mg/dL]", min_value=1.0, max_value=400.0, value=35.0, step=1.0)
            sc = st.number_input("Serum Creatinine (sc) [mg/dL]", min_value=0.1, max_value=75.0, value=1.1, step=0.1, format="%.2f")
            hemo = st.number_input("Hemoglobin (hemo) [g/dL]", min_value=3.0, max_value=20.0, value=14.5, step=0.5)
            pcv = st.number_input("Packed Cell Volume (pcv) [%]", min_value=10.0, max_value=60.0, value=42.0, step=1.0)

        submit_btn = st.form_submit_button("Run Kidney Disease Risk Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_kidney_artifacts()

        input_data = [
            float(vitals_age),
            float(vitals_bp),
            float(sg),
            float(al),
            float(su),
            float(vitals_sugar),
            float(bu),
            float(sc),
            float(hemo),
            float(pcv)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Chronic Kidney Disease (CKD) Risk Detected" if pred == 1 else "No Significant Renal Impairment Detected"

        inputs_dict = {
            "Age": vitals_age,
            "Blood Pressure": f"{vitals_bp} mmHg",
            "Urinary Specific Gravity": sg,
            "Urinary Albumin Grade": al,
            "Urinary Sugar Grade": su,
            "Blood Glucose": f"{vitals_sugar:.1f} mg/dL",
            "Blood Urea": f"{bu:.1f} mg/dL",
            "Serum Creatinine": f"{sc:.2f} mg/dL",
            "Hemoglobin": f"{hemo:.1f} g/dL",
            "Packed Cell Volume": f"{pcv:.1f}%"
        }

        rec = recommendations.get_recommendation("Chronic Kidney Disease", risk_level)

        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Chronic Kidney Disease",
            result_text=result_title,
            risk_level=risk_level,
            inputs_dict=inputs_dict,
            advice=rec["summary"]
        )

        badge_bg = "#FEE2E2" if risk_level == "High" else "#DCFCE7"
        badge_color = "#991B1B" if risk_level == "High" else "#166534"
        border_color = "#EF4444" if risk_level == "High" else "#22C55E"

        st.markdown(f"""
            <div style="background: {badge_bg}; border: 2px solid {border_color}; border-radius: 12px; padding: 1.5rem; margin: 1.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                    <h3 style="color: {badge_color}; margin: 0; font-size: 1.4rem;">
                        {result_title}
                    </h3>
                    <span style="background: {badge_color}; color: white; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 0.9rem;">
                        {risk_level.upper()} RISK ({prob * 100:.1f}%)
                    </span>
                </div>
                <p style="color: #334155; margin-top: 0.8rem; font-size: 1rem; line-height: 1.5;">
                    {rec['summary']}
                </p>
            </div>
        """, unsafe_allow_html=True)

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### 🥗 Renal Protection & Lifestyle")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Acute Renal Red Flags")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Nephrologist")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> This assessment is an educational screening support tool. Definitive CKD diagnosis requires longitudinal GFR and urinary albumin-to-creatinine testing by a physician.
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Chronic Kidney Disease",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_Kidney_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Chronic Kidney Disease",
            disease_key="kidney",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
