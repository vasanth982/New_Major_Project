"""
Heart Disease Assessment Module for Checkup Buddy (v2).
Pre-fills Age, Sex, Resting BP, and Fasting Blood Sugar from active vitals session.
Predicts risk using Random Forest and provides immediate clinical insights + PDF export.
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
def load_heart_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "heart_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "heart_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_heart_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                ❤️ Cardiovascular Health & Heart Disease Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Evaluates myocardial and coronary risk using clinical hemodynamic indicators and exercise stress markers.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    # Pre-fills from active vitals session
    vitals_age = vitals.get("age", 45)
    vitals_sex_num = 1 if vitals.get("gender") == "Male" else 0
    vitals_bp_sys = vitals.get("blood_pressure_sys", 120)
    vitals_fbs_val = 1 if vitals.get("blood_sugar", 100) > 120 else 0

    st.markdown("""
        <div style="background: #F1F5F9; border-left: 4px solid #3B82F6; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #334155;">
            <b>Intake Data Linked:</b> Age (<b>{}</b>), Sex (<b>{}</b>), Resting BP (<b>{} mmHg</b>), Fasting Blood Sugar > 120 mg/dL (<b>{}</b>) have been auto-populated from your intake.
        </div>
    """.format(
        vitals_age,
        "Male" if vitals_sex_num == 1 else "Female",
        vitals_bp_sys,
        "Yes" if vitals_fbs_val == 1 else "No"
    ), unsafe_allow_html=True)

    # ── Chest X-ray / ECG Image Upload (Optional) ─────────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Heart Disease", key_suffix="heart", modality="Chest X-ray / ECG Image")

    st.markdown("---")

    with st.form("heart_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.text_input("Age (Years)", value=str(vitals_age), disabled=True)
            st.text_input("Sex", value="Male" if vitals_sex_num == 1 else "Female", disabled=True)
            cp_options = {
                0: "Typical Angina (0)",
                1: "Atypical Angina (1)",
                2: "Non-anginal Pain (2)",
                3: "Asymptomatic (3)"
            }
            cp = st.selectbox("Chest Pain Type (cp)", options=list(cp_options.keys()), format_func=lambda x: cp_options[x], index=0)
            st.text_input("Resting Blood Pressure (trestbps)", value=f"{vitals_bp_sys} mmHg", disabled=True)

        with col2:
            chol = st.number_input("Serum Cholesterol (chol) [mg/dL]", min_value=80, max_value=600, value=220, step=1)
            st.text_input("Fasting Blood Sugar > 120 mg/dL (fbs)", value="True (>120)" if vitals_fbs_val == 1 else "False (≤120)", disabled=True)
            restecg_options = {
                0: "Normal (0)",
                1: "ST-T Wave Abnormality (1)",
                2: "Left Ventricular Hypertrophy (2)"
            }
            restecg = st.selectbox("Resting ECG Results", options=list(restecg_options.keys()), format_func=lambda x: restecg_options[x], index=0)
            thalach = st.number_input("Max Heart Rate Achieved (thalach)", min_value=60, max_value=230, value=150, step=1)

        with col3:
            exang = st.selectbox("Exercise Induced Angina (exang)", options=[0, 1], format_func=lambda x: "Yes (1)" if x == 1 else "No (0)", index=0)
            oldpeak = st.number_input("ST Depression Induced by Exercise (oldpeak)", min_value=0.0, max_value=8.0, value=1.0, step=0.1, format="%.1f")
            slope = st.selectbox("Slope of Peak Exercise ST Segment", options=[0, 1, 2], format_func=lambda x: {0: "Upsloping (0)", 1: "Flat (1)", 2: "Downsloping (2)"}[x], index=1)
            ca = st.selectbox("Number of Major Vessels Colored by Fluoroscopy (0-3)", options=[0, 1, 2, 3], index=0)
            thal_options = {1: "Normal (1)", 2: "Fixed Defect (2)", 3: "Reversible Defect (3)"}
            thal = st.selectbox("Thalassemia (thal)", options=[1, 2, 3], format_func=lambda x: thal_options[x], index=1)

        submit_btn = st.form_submit_button("Run Heart Disease Risk Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_heart_artifacts()

        input_data = [
            float(vitals_age),
            float(vitals_sex_num),
            float(cp),
            float(vitals_bp_sys),
            float(chol),
            float(vitals_fbs_val),
            float(restecg),
            float(thalach),
            float(exang),
            float(oldpeak),
            float(slope),
            float(ca),
            float(thal)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Cardiovascular Risk Detected" if pred == 1 else "No Significant Heart Disease Risk Detected"

        # Prepare inputs dictionary for reporting and audit
        inputs_dict = {
            "Age": vitals_age,
            "Sex": "Male" if vitals_sex_num == 1 else "Female",
            "Chest Pain Type": cp_options[cp],
            "Resting BP": f"{vitals_bp_sys} mmHg",
            "Serum Cholesterol": f"{chol} mg/dL",
            "Fasting Blood Sugar > 120": "Yes" if vitals_fbs_val == 1 else "No",
            "Resting ECG": restecg_options[restecg],
            "Max Heart Rate": f"{thalach} bpm",
            "Exercise Angina": "Yes" if exang == 1 else "No",
            "ST Depression": f"{oldpeak:.1f}",
            "ST Slope": slope,
            "Fluoroscopy Vessels": ca,
            "Thalassemia": thal_options[thal]
        }

        rec = recommendations.get_recommendation("Heart Disease", risk_level)

        # Save to SQLite database
        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Heart Disease",
            result_text=result_title,
            risk_level=risk_level,
            inputs_dict=inputs_dict,
            advice=rec["summary"]
        )

        # Display result card
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
            st.markdown("#### 🥗 Lifestyle & Preventative Actions")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Warning Signs Requiring Attention")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Physician")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> This assessment is an educational and screening support tool powered by machine learning. It is not an official medical diagnosis or clinical substitute for evaluation by a licensed cardiologist.
            </div>
        """, unsafe_allow_html=True)

        # PDF Download Button
        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Heart Disease",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_Heart_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Heart Disease",
            disease_key="heart",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
