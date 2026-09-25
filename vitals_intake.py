"""
Mandatory Vitals Intake Flow for Checkup Buddy (v2).
Enforces Step 1 (Identity) and Step 2 (Core Vitals) before any diagnostic module can run.
Persists session data to SQLite and pre-fills relevant parameters for disease models.
"""

import streamlit as st
import database
import i18n


def calculate_bmi(height_cm: float, weight_kg: float) -> tuple[float, str]:
    """Calculates BMI and returns (bmi_value, category_label)."""
    if not height_cm or not weight_kg or height_cm <= 0 or weight_kg <= 0:
        return 0.0, "N/A"
    
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m * height_m)
    bmi_rounded = round(bmi, 1)

    if bmi_rounded < 18.5:
        category = "Underweight (<18.5)"
    elif bmi_rounded < 25.0:
        category = "Normal (18.5 - 24.9)"
    elif bmi_rounded < 30.0:
        category = "Overweight (25.0 - 29.9)"
    else:
        category = "Obese (≥30.0)"

    return bmi_rounded, category


def render_vitals_banner():
    """Renders a concise visual banner showing currently active vitals session."""
    active = st.session_state.get("active_vitals")
    if not active:
        return

    bmi_text = f"{active.get('bmi', 'N/A')}" if active.get('bmi') else "N/A"
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #CCFBF1, #DBEAFE); border: 1px solid #99F6E4;
                    border-radius: 12px; padding: 0.9rem 1.2rem; margin-bottom: 1.5rem; display: flex;
                    align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="font-weight: 700; color: #0D9488; font-size: 1rem;">
                    {i18n.t("active_vitals_banner")}: {active['patient_name']} ({active['age']}y, {active['gender']})
                </span>
                <div style="display: flex; gap: 15px; margin-top: 4px; font-size: 0.85rem; color: #0F766E; flex-wrap: wrap;">
                    <span>🌡️ {i18n.t("field_temp")}: <b>{active['body_temp']}°C</b></span>
                    <span>💓 BP: <b>{active['blood_pressure_sys']}/{active['blood_pressure_dia']} mmHg</b></span>
                    <span>🩸 {i18n.t("field_blood_sugar")}: <b>{active['blood_sugar']} mg/dL</b></span>
                    <span>⚖️ {i18n.t("field_bmi")}: <b>{bmi_text}</b></span>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="background: #10B981; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">
                    {i18n.t("gated_intake_passed")}
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_vitals_intake_page():
    """Renders the mandatory intake form and manages validation gating."""
    user_id = st.session_state.get("user_id")
    profile = database.get_profile(user_id) if user_id else {}

    # ── Welcome banner shown only immediately after account creation ──
    if st.session_state.get("signup_just_completed"):
        username = st.session_state.get("username", "")
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #DCFCE7, #EFF6FF); border: 2px solid #86EFAC;
                        border-radius: 14px; padding: 1.8rem 2rem; margin-bottom: 2rem; text-align: center;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎉</div>
                <h2 style="color: #15803D; font-weight: 800; margin: 0 0 0.4rem 0;">
                    Welcome to Checkup Buddy, {username}!
                </h2>
                <p style="color: #166534; font-size: 1rem; margin: 0 0 1rem 0;">
                    Your account has been successfully created and your email is verified.
                </p>
                <p style="color: #334155; font-size: 0.92rem; margin: 0;">
                    To unlock all diagnostic modules, please complete your <strong>Mandatory Vitals Intake</strong> below.
                    This takes about 2 minutes and pre-fills your health data across all disease assessments.
                </p>
            </div>
        """, unsafe_allow_html=True)
        # Clear the flag so the banner only shows once
        st.session_state.pop("signup_just_completed", None)

    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="color: #0D9488; font-weight: 700; margin-bottom: 0.3rem;">
                {i18n.t("vitals_title")}
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                {i18n.t("vitals_subtitle")}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Check if there's already an active intake session
    if st.session_state.get("active_vitals"):
        render_vitals_banner()
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            st.info(i18n.t("vitals_subtitle"))
        with col_btn2:
            if st.button(i18n.t("btn_retake_vitals"), use_container_width=True):
                st.session_state.active_vitals = None
                st.session_state.vitals_completed = False
                st.rerun()

        if st.session_state.get("active_vitals"):
            return

    # Pre-fill defaults from user profile if available
    default_name = profile.get("full_name") or profile.get("username") or ""
    default_age = profile.get("age") or 30
    gender_options = ["Male", "Female", "Other", "Prefer not to say"]
    default_gender_idx = 0
    if profile.get("gender") in gender_options:
        default_gender_idx = gender_options.index(profile["gender"])

    with st.form("vitals_intake_form"):
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.8rem;">
                <span style="background: #0D9488; color: white; width: 26px; height: 26px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;">1</span>
                <h4 style="margin: 0; color: #0F172A;">{i18n.t("step1_title")}</h4>
            </div>
        """, unsafe_allow_html=True)

        col_id1, col_id2, col_id3 = st.columns([2, 1, 1])
        with col_id1:
            patient_name = st.text_input(f"{i18n.t('field_full_name')} *", value=default_name, placeholder="e.g. John Doe").strip()
        with col_id2:
            age = st.number_input(f"{i18n.t('field_age')} *", min_value=1, max_value=120, value=int(default_age))
        with col_id3:
            gender_options_t = [i18n.t("gender_male"), i18n.t("gender_female"), i18n.t("gender_other"), "Prefer not to say"]
            gender = st.selectbox(f"{i18n.t('field_gender')} *", options=gender_options_t, index=default_gender_idx)

        st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.8rem;">
                <span style="background: #0D9488; color: white; width: 26px; height: 26px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;">2</span>
                <h4 style="margin: 0; color: #0F172A;">{i18n.t("step2_title")}</h4>
            </div>
        """, unsafe_allow_html=True)

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            body_temp = st.number_input(f"{i18n.t('field_temp')} *", min_value=25.0, max_value=48.0, value=36.8, step=0.1, format="%.1f")
            st.caption("Standard physiological range: 30.0°C – 45.0°C")
        with col_v2:
            bp_sys = st.number_input(f"{i18n.t('field_bp_sys')} *", min_value=40, max_value=300, value=120, step=1)
            st.caption("Standard range: 60 – 250 mmHg")
        with col_v3:
            bp_dia = st.number_input(f"{i18n.t('field_bp_dia')} *", min_value=20, max_value=200, value=80, step=1)
            st.caption("Standard range: 40 – 150 mmHg")

        col_v4, col_v5, col_v6 = st.columns(3)
        with col_v4:
            blood_sugar = st.number_input(f"{i18n.t('field_blood_sugar')} *", min_value=20.0, max_value=700.0, value=95.0, step=1.0)
            st.caption("Standard range: 40.0 – 600.0 mg/dL")
        with col_v5:
            height_cm = st.number_input(f"{i18n.t('field_height')} (Optional)", min_value=0.0, max_value=260.0, value=170.0, step=0.5)
            st.caption(i18n.t("field_bmi"))
        with col_v6:
            weight_kg = st.number_input(f"{i18n.t('field_weight')} (Optional)", min_value=0.0, max_value=300.0, value=70.0, step=0.5)
            st.caption(i18n.t("field_bmi"))

        # Dynamic BMI Preview
        bmi_val, bmi_cat = calculate_bmi(height_cm, weight_kg)
        if bmi_val > 0:
            st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 0.6rem 1rem; margin: 1rem 0; font-size: 0.9rem; color: #334155;">
                    💡 <b>Calculated Body Mass Index (BMI):</b> <span style="font-weight: 700; color: #2563EB;">{bmi_val} kg/m²</span> — <i>{bmi_cat}</i>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        submit_vitals = st.form_submit_button(i18n.t("btn_save_vitals"), type="primary", use_container_width=True)

        if submit_vitals:
            errors = []
            if not patient_name.strip():
                errors.append("Patient Name is required.")
            if not (0 < age <= 120):
                errors.append("Enter a valid age between 1 and 120.")
            if not (30.0 <= body_temp <= 45.0):
                errors.append("Body temperature out of expected range (30–45°C).")
            if not (60 <= bp_sys <= 250 and 40 <= bp_dia <= 150):
                errors.append("Blood pressure out of expected range (Systolic: 60-250, Diastolic: 40-150 mmHg).")
            if bp_dia >= bp_sys:
                errors.append("Diastolic pressure cannot be greater than or equal to Systolic pressure.")
            if not (40.0 <= blood_sugar <= 600.0):
                errors.append("Blood sugar out of expected range (40–600 mg/dL).")

            if errors:
                for err in errors:
                    st.error(f"⚠️ {err}")
                return

            # Save session to SQLite
            session_id = database.create_vitals_session(
                user_id=user_id,
                patient_name=patient_name.strip(),
                age=int(age),
                gender=gender,
                body_temp=float(body_temp),
                bp_sys=int(bp_sys),
                bp_dia=int(bp_dia),
                blood_sugar=float(blood_sugar),
                height_cm=float(height_cm) if height_cm > 0 else None,
                weight_kg=float(weight_kg) if weight_kg > 0 else None
            )

            # Store in session state for pre-filling diagnostic modules
            st.session_state.active_vitals = {
                "session_id": session_id,
                "patient_name": patient_name.strip(),
                "age": int(age),
                "gender": gender,
                "body_temp": float(body_temp),
                "blood_pressure_sys": int(bp_sys),
                "blood_pressure_dia": int(bp_dia),
                "blood_sugar": float(blood_sugar),
                "height_cm": float(height_cm) if height_cm > 0 else None,
                "weight_kg": float(weight_kg) if weight_kg > 0 else None,
                "bmi": bmi_val if bmi_val > 0 else None
            }
            st.session_state.vitals_completed = True

            st.success(i18n.t("vitals_saved_success"))
            st.rerun()
