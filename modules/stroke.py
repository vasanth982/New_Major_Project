"""
Stroke Risk Assessment Module for Checkup Buddy (v2).
Pre-fills Age, Gender, Hypertension (from BP), Glucose, and BMI from active vitals session.
Predicts cerebrovascular stroke probability using Random Forest and provides immediate clinical insights + PDF export.
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
def load_stroke_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "stroke_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "stroke_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_stroke_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                🧠 Cerebrovascular Stroke Risk Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Evaluates acute cerebrovascular risk based on hemodynamic hypertension status, glycemic load, cardiac history, and lifestyle factors.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    # Pre-fills from active vitals session
    vitals_age = vitals.get("age", 50)
    vitals_gender_str = vitals.get("gender", "Male")
    vitals_gender_num = 1 if vitals_gender_str == "Male" else 0
    bp_sys = vitals.get("blood_pressure_sys", 120)
    bp_dia = vitals.get("blood_pressure_dia", 80)
    # Clinical stage 1 hypertension criteria: >= 130 sys or >= 80 dia, or >= 140/90
    hypertension_auto = 1 if (bp_sys >= 130 or bp_dia >= 85) else 0
    vitals_glucose = vitals.get("blood_sugar", 100.0)
    vitals_bmi = vitals.get("bmi") or 27.0

    st.markdown("""
        <div style="background: #F1F5F9; border-left: 4px solid #3B82F6; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #334155;">
            <b>Intake Data Linked:</b> Gender (<b>{}</b>), Age (<b>{}</b>), Hypertension Flag (<b>{} based on {}/{} mmHg</b>), Glucose (<b>{} mg/dL</b>), BMI (<b>{} kg/m²</b>) pre-populated from intake.
        </div>
    """.format(
        vitals_gender_str,
        vitals_age,
        "Hypertensive Risk" if hypertension_auto == 1 else "Normal Range",
        bp_sys,
        bp_dia,
        vitals_glucose,
        vitals_bmi
    ), unsafe_allow_html=True)

    # ── X-ray / Neuroimaging Upload (Optional) ─────────────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Stroke Risk", key_suffix="stroke", modality="X-ray / Brain Scan")

    with st.form("stroke_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Biological Gender", value=vitals_gender_str, disabled=True)
            st.text_input("Age (Years)", value=str(vitals_age), disabled=True)
            st.text_input("Hypertension Indicator", value="Yes (BP ≥ 130/85)" if hypertension_auto == 1 else "No (< 130/85)", disabled=True)
            heart_disease = st.selectbox("Pre-existing Heart Disease History", options=[0, 1], format_func=lambda x: "Yes (1)" if x == 1 else "No (0)", index=0)

        with col2:
            st.text_input("Average Glucose Level (mg/dL)", value=f"{vitals_glucose:.1f}", disabled=True)
            st.text_input("Body Mass Index (BMI)", value=f"{vitals_bmi:.1f}", disabled=True)
            ever_married = st.selectbox("Ever Married", options=[1, 0], format_func=lambda x: "Yes" if x == 1 else "No", index=0)
            smoking_options = {
                0: "Never Smoked (0)",
                1: "Formerly Smoked (1)",
                2: "Currently Smokes (2)",
                3: "Unknown / Unspecified (3)"
            }
            smoking = st.selectbox("Smoking Status", options=list(smoking_options.keys()), format_func=lambda x: smoking_options[x], index=0)

        submit_btn = st.form_submit_button("Run Stroke Risk Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_stroke_artifacts()

        input_data = [
            float(vitals_gender_num),
            float(vitals_age),
            float(hypertension_auto),
            float(heart_disease),
            float(ever_married),
            float(vitals_glucose),
            float(vitals_bmi),
            float(smoking)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Cerebrovascular Stroke Risk Detected" if pred == 1 else "No Significant Stroke Risk Indicators"

        inputs_dict = {
            "Gender": vitals_gender_str,
            "Age": vitals_age,
            "Hypertension Status": "Present" if hypertension_auto == 1 else "Normal",
            "Heart Disease History": "Yes" if heart_disease == 1 else "No",
            "Average Glucose": f"{vitals_glucose:.1f} mg/dL",
            "Body Mass Index (BMI)": f"{vitals_bmi:.1f} kg/m²",
            "Ever Married": "Yes" if ever_married == 1 else "No",
            "Smoking History": smoking_options[smoking]
        }

        rec = recommendations.get_recommendation("Stroke Risk", risk_level)

        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Stroke Risk",
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
            st.markdown("#### 🏃 Vascular Risk Management")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Acute BE-FAST Warning Signs")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Vascular Specialist")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> Acute stroke is a medical emergency. If sudden facial drooping, arm numbness, or speech slurring occurs, call emergency services (911) immediately without delay.
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Stroke Risk",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_Stroke_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Stroke Risk",
            disease_key="stroke",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
