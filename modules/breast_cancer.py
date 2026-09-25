"""
Breast Cancer Risk Assessment Module for Checkup Buddy (v2).
Evaluates Fine-Needle Aspiration (FNA) nuclear morphology indicators using Random Forest.
Accessible to all genders with clinical validation disclaimer for female populations.
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
def load_breast_cancer_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "breast_cancer_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "breast_cancer_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_breast_cancer_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                🎗️ Breast Cancer Cytology & Tumor Morphology Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Evaluates nuclear morphometry features derived from digitized Fine-Needle Aspiration (FNA) biopsy samples.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    patient_gender = vitals.get("gender", "Female")

    # Demographic / clinical population note per Section 6 requirements
    st.markdown(f"""
        <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #92400E;">
            ℹ️ <b>Demographic Validation Notice:</b> Patient Gender is recorded as <b>{patient_gender}</b>. While this assessment is accessible to all genders, please note that the underlying Wisconsin Diagnostic Breast Cancer (WDBC) dataset is primarily validated on female clinical cohorts.
        </div>
    """, unsafe_allow_html=True)

    # ── Mammography / X-ray Image Upload (Optional) ───────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Breast Cancer", key_suffix="breast", modality="X-ray / Mammography Image")

    st.markdown("---")

    preset = st.selectbox("Cytology Sample Presets", options=["Custom Cytology Data", "Typical Benign Aspirate Sample", "High-Suspicion Malignant Sample"])

    if preset == "Typical Benign Aspirate Sample":
        d_rad, d_tex, d_per, d_area = 12.32, 12.39, 78.83, 464.1
        d_smt, d_cmp, d_con, d_cp = 0.10280, 0.06981, 0.03987, 0.03700
        d_sym, d_fd = 0.1959, 0.05955
    elif preset == "High-Suspicion Malignant Sample":
        d_rad, d_tex, d_per, d_area = 17.99, 10.38, 122.80, 1001.0
        d_smt, d_cmp, d_con, d_cp = 0.11840, 0.27760, 0.30010, 0.14710
        d_sym, d_fd = 0.2419, 0.07871
    else:
        d_rad, d_tex, d_per, d_area = 14.12, 19.28, 91.96, 654.88
        d_smt, d_cmp, d_con, d_cp = 0.096, 0.104, 0.088, 0.048
        d_sym, d_fd = 0.181, 0.062

    with st.form("breast_cancer_form"):
        col1, col2 = st.columns(2)

        with col1:
            mean_radius = st.number_input("Mean Nuclear Radius (mean radius)", min_value=5.0, max_value=40.0, value=float(d_rad), step=0.1, format="%.2f")
            mean_texture = st.number_input("Mean Texture - Gray-scale variation (mean texture)", min_value=5.0, max_value=50.0, value=float(d_tex), step=0.1, format="%.2f")
            mean_perimeter = st.number_input("Mean Perimeter (mean perimeter)", min_value=30.0, max_value=250.0, value=float(d_per), step=0.5, format="%.2f")
            mean_area = st.number_input("Mean Nuclear Area (mean area)", min_value=100.0, max_value=3000.0, value=float(d_area), step=5.0, format="%.1f")
            mean_smoothness = st.number_input("Mean Smoothness - Local variations in radius (mean smoothness)", min_value=0.01, max_value=0.3, value=float(d_smt), step=0.005, format="%.5f")

        with col2:
            mean_compactness = st.number_input("Mean Compactness (perimeter² / area - 1.0)", min_value=0.01, max_value=0.5, value=float(d_cmp), step=0.005, format="%.5f")
            mean_concavity = st.number_input("Mean Concavity - Severity of concave contours", min_value=0.0, max_value=0.6, value=float(d_con), step=0.005, format="%.5f")
            mean_concave_points = st.number_input("Mean Concave Points - Number of concave portions", min_value=0.0, max_value=0.3, value=float(d_cp), step=0.005, format="%.5f")
            mean_symmetry = st.number_input("Mean Nuclear Symmetry", min_value=0.05, max_value=0.5, value=float(d_sym), step=0.005, format="%.4f")
            mean_fractal_dim = st.number_input("Mean Fractal Dimension ('coastline approximation' - 1)", min_value=0.01, max_value=0.2, value=float(d_fd), step=0.002, format="%.5f")

        submit_btn = st.form_submit_button("Run Breast Cytology Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_breast_cancer_artifacts()

        input_data = [
            float(mean_radius),
            float(mean_texture),
            float(mean_perimeter),
            float(mean_area),
            float(mean_smoothness),
            float(mean_compactness),
            float(mean_concavity),
            float(mean_concave_points),
            float(mean_symmetry),
            float(mean_fractal_dim)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Cytological Malignancy Risk Detected" if pred == 1 else "Benign Cytological Characteristics Detected"

        inputs_dict = {
            "Mean Radius": f"{mean_radius:.2f}",
            "Mean Texture": f"{mean_texture:.2f}",
            "Mean Perimeter": f"{mean_perimeter:.2f}",
            "Mean Area": f"{mean_area:.1f}",
            "Mean Smoothness": f"{mean_smoothness:.5f}",
            "Mean Compactness": f"{mean_compactness:.5f}",
            "Mean Concavity": f"{mean_concavity:.5f}",
            "Mean Concave Points": f"{mean_concave_points:.5f}",
            "Mean Symmetry": f"{mean_symmetry:.4f}",
            "Mean Fractal Dimension": f"{mean_fractal_dim:.5f}"
        }

        rec = recommendations.get_recommendation("Breast Cancer Risk", risk_level)

        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Breast Cancer Risk",
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

        col_g1, col_g2 = col1, col2 = st.columns(2)
        with col_g1:
            st.markdown("#### 🎗️ Screening & Clinical Follow-up")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Physical Warning Signs Requiring Assessment")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Surgical Oncologist")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> Cytological evaluation tools are assistive. Formal histological tissue confirmation via core-needle biopsy or diagnostic imaging is essential for staging and therapy.
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Breast Cancer Risk",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_BreastCancer_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Breast Cancer",
            disease_key="breast_cancer",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
