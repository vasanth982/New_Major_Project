"""
Diabetes Assessment Module for Checkup Buddy (v2).
Pre-fills Glucose, Blood Pressure, BMI, and Age from active vitals session.
Predicts glycemic risk using Random Forest and provides immediate clinical insights + PDF export.
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
def load_diabetes_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "diabetes_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "diabetes_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_diabetes_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                🩸 Glycemic Profile & Diabetes Risk Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Evaluates Type-2 diabetes predisposition utilizing fasting glucose, metabolic indicators, and body mass index.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    # Pre-fills from active vitals session
    vitals_age = vitals.get("age", 35)
    vitals_glucose = vitals.get("blood_sugar", 100.0)
    vitals_bp_dia = vitals.get("blood_pressure_dia", 75)
    vitals_bmi = vitals.get("bmi") or 26.5
    is_male = vitals.get("gender") == "Male"

    st.markdown("""
        <div style="background: #F1F5F9; border-left: 4px solid #3B82F6; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #334155;">
            <b>Intake Data Linked:</b> Fasting Glucose (<b>{} mg/dL</b>), Diastolic BP (<b>{} mmHg</b>), BMI (<b>{} kg/m²</b>), Age (<b>{}</b>) have been pre-filled from your intake session.
        </div>
    """.format(vitals_glucose, vitals_bp_dia, vitals_bmi, vitals_age), unsafe_allow_html=True)

    # ── X-ray / Medical Imaging Upload (Optional) ─────────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Diabetes", key_suffix="diabetes", modality="X-ray Image")

    with st.form("diabetes_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Fasting Glucose (mg/dL)", value=f"{vitals_glucose:.1f}", disabled=True)
            st.text_input("Diastolic Blood Pressure (mmHg)", value=f"{vitals_bp_dia}", disabled=True)
            st.text_input("Body Mass Index (BMI)", value=f"{vitals_bmi:.1f}", disabled=True)
            st.text_input("Age (Years)", value=str(vitals_age), disabled=True)

        with col2:
            if is_male:
                pregnancies = 0
                st.text_input("Pregnancies", value="0 (N/A for Male)", disabled=True)
            else:
                pregnancies = st.number_input("Number of Pregnancies", min_value=0, max_value=20, value=1, step=1)

            skin_thickness = st.number_input("Triceps Skinfold Thickness (mm)", min_value=0.0, max_value=99.0, value=25.0, step=1.0)
            insulin = st.number_input("2-Hour Serum Insulin (μU/mL)", min_value=0.0, max_value=900.0, value=85.0, step=5.0)
            pedigree = st.number_input("Diabetes Pedigree Function (family history score)", min_value=0.05, max_value=2.5, value=0.45, step=0.05, format="%.2f")

        submit_btn = st.form_submit_button("Run Diabetes Risk Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_diabetes_artifacts()

        input_data = [
            float(pregnancies),
            float(vitals_glucose),
            float(vitals_bp_dia),
            float(skin_thickness),
            float(insulin),
            float(vitals_bmi),
            float(pedigree),
            float(vitals_age)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Diabetes Risk Detected" if pred == 1 else "No Significant Diabetes Risk Detected"

        inputs_dict = {
            "Pregnancies": pregnancies,
            "Fasting Glucose": f"{vitals_glucose:.1f} mg/dL",
            "Diastolic Blood Pressure": f"{vitals_bp_dia} mmHg",
            "Triceps Skinfold": f"{skin_thickness:.1f} mm",
            "Serum Insulin": f"{insulin:.1f} μU/mL",
            "Body Mass Index (BMI)": f"{vitals_bmi:.1f} kg/m²",
            "Diabetes Pedigree Function": f"{pedigree:.2f}",
            "Age": vitals_age
        }

        rec = recommendations.get_recommendation("Diabetes", risk_level)

        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Diabetes",
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
            st.markdown("#### 🥗 Lifestyle & Nutritional Interventions")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Acute Glycemic Warning Signs")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Endocrinologist")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> This assessment is an educational screening support tool. It is not an official medical diagnosis of Diabetes Mellitus.
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Diabetes",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_Diabetes_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Diabetes",
            disease_key="diabetes",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
