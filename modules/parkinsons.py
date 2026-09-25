"""
Parkinson's Disease Assessment Module for Checkup Buddy (v2).
Evaluates 22 biomedical voice acoustic features using Support Vector Machine (SVM).
Provides immediate clinical insights + PDF export.
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
def load_parkinsons_artifacts():
    model_path = os.path.join(SAVED_MODELS_DIR, "parkinsons_model.sav")
    scaler_path = os.path.join(SAVED_MODELS_DIR, "parkinsons_scaler.sav")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def render_parkinsons_module():
    st.markdown("""
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 0.2rem;">
                🧠 Parkinson's Disease Vocal Biomarker Assessment
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Analyzes biomedical voice acoustics, fundamental frequency jitter, and amplitude shimmer to assess motor-speech impairments.
            </p>
        </div>
    """, unsafe_allow_html=True)

    vitals = st.session_state.get("active_vitals")
    if not vitals:
        st.warning("⚠️ Please complete the Mandatory Vitals Intake before accessing this module.")
        return

    st.markdown("""
        <div style="background: #F1F5F9; border-left: 4px solid #3B82F6; padding: 0.75rem 1rem; border-radius: 4px; margin-bottom: 1.2rem; font-size: 0.88rem; color: #334155;">
            <b>Clinical Voice Analysis:</b> Enter the patient's acoustic phonation recordings below. You may also select a clinical sample preset for demonstration.
        </div>
    """, unsafe_allow_html=True)

    # ── X-ray / Neurological Image Upload (Optional) ──────────────────────
    diagnostic_helper.render_xray_uploader(disease_name="Parkinson's Disease", key_suffix="parkinsons", modality="X-ray / Neurological Scan")

    preset = st.selectbox("Clinical Acoustic Sample Presets", options=["Custom Clinical Data", "Typical Healthy Baseline Sample", "Symptomatic Vocal Dysphonia Sample"])

    # Baseline defaults
    if preset == "Typical Healthy Baseline Sample":
        d_fo, d_fhi, d_flo = 197.07, 206.89, 192.05
        d_jit, d_jit_abs, d_rap, d_ppq, d_ddp = 0.00289, 0.00001, 0.00166, 0.00168, 0.00498
        d_shm, d_shm_db, d_apq3, d_apq5, d_apq, d_dda = 0.01098, 0.09700, 0.00563, 0.00680, 0.00802, 0.01689
        d_nhr, d_hnr, d_rpde, d_dfa = 0.00339, 26.775, 0.422229, 0.741367
        d_sp1, d_sp2, d_d2, d_ppe = -7.348300, 0.177551, 1.743867, 0.085569
    elif preset == "Symptomatic Vocal Dysphonia Sample":
        d_fo, d_fhi, d_flo = 119.99, 157.30, 75.00
        d_jit, d_jit_abs, d_rap, d_ppq, d_ddp = 0.00784, 0.00007, 0.00370, 0.00554, 0.01109
        d_shm, d_shm_db, d_apq3, d_apq5, d_apq, d_dda = 0.04374, 0.42600, 0.02182, 0.03130, 0.02971, 0.06545
        d_nhr, d_hnr, d_rpde, d_dfa = 0.02211, 21.033, 0.414783, 0.815285
        d_sp1, d_sp2, d_d2, d_ppe = -4.813031, 0.266482, 2.301442, 0.284654
    else:
        d_fo, d_fhi, d_flo = 150.0, 180.0, 110.0
        d_jit, d_jit_abs, d_rap, d_ppq, d_ddp = 0.004, 0.00003, 0.002, 0.0025, 0.006
        d_shm, d_shm_db, d_apq3, d_apq5, d_apq, d_dda = 0.025, 0.25, 0.012, 0.015, 0.018, 0.036
        d_nhr, d_hnr, d_rpde, d_dfa = 0.015, 23.0, 0.45, 0.72
        d_sp1, d_sp2, d_d2, d_ppe = -5.5, 0.22, 2.1, 0.20

    with st.form("parkinsons_form"):
        st.markdown("##### 1. Fundamental Frequency & Vocal Pitch (Hz)")
        c1, c2, c3 = st.columns(3)
        with c1:
            fo = st.number_input("Average Vocal Pitch MDVP:Fo (Hz)", min_value=50.0, max_value=300.0, value=float(d_fo), step=1.0)
        with c2:
            fhi = st.number_input("Maximum Vocal Pitch MDVP:Fhi (Hz)", min_value=50.0, max_value=600.0, value=float(d_fhi), step=1.0)
        with c3:
            flo = st.number_input("Minimum Vocal Pitch MDVP:Flo (Hz)", min_value=40.0, max_value=300.0, value=float(d_flo), step=1.0)

        st.markdown("##### 2. Frequency Jitter Measurements")
        j1, j2, j3, j4, j5 = st.columns(5)
        with j1:
            jit = st.number_input("MDVP:Jitter(%)", min_value=0.0, max_value=0.1, value=float(d_jit), step=0.001, format="%.5f")
        with j2:
            jit_abs = st.number_input("MDVP:Jitter(Abs)", min_value=0.0, max_value=0.001, value=float(d_jit_abs), step=0.00001, format="%.5f")
        with j3:
            rap = st.number_input("MDVP:RAP", min_value=0.0, max_value=0.1, value=float(d_rap), step=0.001, format="%.5f")
        with j4:
            ppq = st.number_input("MDVP:PPQ", min_value=0.0, max_value=0.1, value=float(d_ppq), step=0.001, format="%.5f")
        with j5:
            ddp = st.number_input("Jitter:DDP", min_value=0.0, max_value=0.2, value=float(d_ddp), step=0.001, format="%.5f")

        st.markdown("##### 3. Amplitude Shimmer Measurements")
        s1, s2, s3, s4, s5, s6 = st.columns(6)
        with s1:
            shm = st.number_input("MDVP:Shimmer", min_value=0.0, max_value=0.3, value=float(d_shm), step=0.005, format="%.5f")
        with s2:
            shm_db = st.number_input("Shimmer(dB)", min_value=0.0, max_value=2.0, value=float(d_shm_db), step=0.01, format="%.4f")
        with s3:
            apq3 = st.number_input("Shimmer:APQ3", min_value=0.0, max_value=0.2, value=float(d_apq3), step=0.005, format="%.5f")
        with s4:
            apq5 = st.number_input("Shimmer:APQ5", min_value=0.0, max_value=0.2, value=float(d_apq5), step=0.005, format="%.5f")
        with s5:
            apq = st.number_input("MDVP:APQ", min_value=0.0, max_value=0.2, value=float(d_apq), step=0.005, format="%.5f")
        with s6:
            dda = st.number_input("Shimmer:DDA", min_value=0.0, max_value=0.5, value=float(d_dda), step=0.01, format="%.5f")

        st.markdown("##### 4. Harmonicity & Non-Linear Complexity")
        n1, n2, n3, n4, n5, n6, n7, n8 = st.columns(8)
        with n1:
            nhr = st.number_input("NHR", value=float(d_nhr), step=0.005, format="%.5f")
        with n2:
            hnr = st.number_input("HNR", value=float(d_hnr), step=1.0, format="%.2f")
        with n3:
            rpde = st.number_input("RPDE", value=float(d_rpde), step=0.05, format="%.4f")
        with n4:
            dfa = st.number_input("DFA", value=float(d_dfa), step=0.05, format="%.4f")
        with n5:
            sp1 = st.number_input("spread1", value=float(d_sp1), step=0.5, format="%.2f")
        with n6:
            sp2 = st.number_input("spread2", value=float(d_sp2), step=0.05, format="%.4f")
        with n7:
            d2 = st.number_input("D2", value=float(d_d2), step=0.1, format="%.3f")
        with n8:
            ppe = st.number_input("PPE", value=float(d_ppe), step=0.05, format="%.4f")

        submit_btn = st.form_submit_button("Run Parkinson's Vocal Diagnostic", type="primary", use_container_width=True)

    if submit_btn:
        model, scaler = load_parkinsons_artifacts()

        input_data = [
            float(fo), float(fhi), float(flo), float(jit), float(jit_abs),
            float(rap), float(ppq), float(ddp), float(shm), float(shm_db),
            float(apq3), float(apq5), float(apq), float(dda), float(nhr),
            float(hnr), float(rpde), float(dfa), float(sp1), float(sp2),
            float(d2), float(ppe)
        ]

        scaled = scaler.transform([input_data])
        pred = model.predict(scaled)[0]
        prob = model.predict_proba(scaled)[0][1]

        risk_level = "High" if pred == 1 else "Low"
        result_title = "Elevated Parkinson's Acoustic Biomarkers Detected" if pred == 1 else "No Significant Parkinson's Vocal Dysphonia Detected"

        inputs_dict = {
            "Mean Pitch (Fo)": f"{fo:.1f} Hz",
            "Pitch Range": f"{flo:.1f} - {fhi:.1f} Hz",
            "Jitter (%)": f"{jit:.5f}",
            "Shimmer": f"{shm:.5f}",
            "Noise-to-Harmonics (NHR)": f"{nhr:.5f}",
            "Harmonics-to-Noise (HNR)": f"{hnr:.2f} dB",
            "RPDE Complexity": f"{rpde:.4f}",
            "D2 Fractal Dimension": f"{d2:.3f}",
            "PPE Pitch Period Entropy": f"{ppe:.4f}"
        }

        rec = recommendations.get_recommendation("Parkinson's Disease", risk_level)

        user_id = st.session_state.get("user_id")
        record_id = database.save_prediction(
            user_id=user_id,
            vitals_session_id=vitals.get("session_id"),
            disease="Parkinson's Disease",
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
            st.markdown("#### 🏃 Motor Rehabilitation & Vocal Therapy")
            for item in rec["lifestyle"]:
                st.markdown(f"- {item}")

        with col_g2:
            st.markdown("#### 🚨 Neurological Warning Signs")
            for item in rec["urgent_signs"]:
                st.markdown(f"- {item}")

        st.markdown("#### 👨‍⚕️ Questions for Your Neurologist")
        for q in rec["doctor_questions"]:
            st.markdown(f"- *\"{q}\"*")

        st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.8rem; margin: 1.5rem 0; font-size: 0.82rem; color: #64748B;">
                ⚖️ <b>Clinical Disclaimer:</b> Acoustic analysis is a non-invasive screening technique and cannot replace a clinical physical and neurological exam.
            </div>
        """, unsafe_allow_html=True)

        pdf_bytes = pdf_generator.generate_clinical_pdf(
            patient_name=vitals["patient_name"],
            patient_id=user_id,
            age=vitals["age"],
            gender=vitals["gender"],
            vitals=vitals,
            disease_name="Parkinson's Disease",
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            inputs_dict=inputs_dict,
            recommendation=rec
        )

        st.download_button(
            label="📄 Download Hospital-Grade PDF Report",
            data=pdf_bytes,
            file_name=f"CheckupBuddy_Parkinsons_Report_{vitals['patient_name'].replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        # Auto-email report to user's registered email
        diagnostic_helper.auto_send_diagnosis_email(
            user_id=user_id,
            vitals=vitals,
            disease_name="Parkinson's Disease",
            disease_key="parkinsons",
            record_id=record_id,
            result_title=result_title,
            risk_level=risk_level,
            confidence_pct=round(prob * 100, 1),
            pdf_bytes=pdf_bytes
        )
