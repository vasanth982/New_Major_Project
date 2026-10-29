"""
Checkup Buddy (v2) — Multi-Disease Health Analytics & Preventive Diagnostic Platform.
Main Streamlit application entrypoint, role-based page router, and aesthetic shell.
"""

import os
import json
import pandas as pd
import streamlit as st

# Load environment variables if .env file exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Streamlit Page Config
st.set_page_config(
    page_title="Checkup Buddy | Clinical AI Health Analytics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core imports
import database
import auth
import otp_service
import profile
import vitals_intake
import owner_dashboard
import pdf_generator
import recommendations
import i18n

# Module imports
from modules import heart, diabetes, parkinsons, kidney, liver, stroke, breast_cancer

# Initialize database tables on app startup
database.init_db()

# Auto-seed owner from environment if configured
auth.auto_seed_owner_from_env()

# Log SMTP configuration state at startup so Render logs immediately show
# whether email credentials are configured correctly.
otp_service._log_smtp_config_state()


def inject_custom_styles():
    """Injects the full clinical healthcare CSS from style.css plus minimal overrides."""
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    else:
        # Inline minimal fallback
        st.markdown("""
            <style>
            @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600;700&display=swap');
            html, body, [class*="css"] {
                font-family: 'Plus Jakarta Sans', 'Noto Sans Devanagari', 'Noto Sans Tamil', 'Nirmala UI', sans-serif !important;
            }
            div.stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #0D9488 0%, #1E3A8A 100%) !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 14px rgba(13, 148, 136, 0.25) !important;
                transition: all 0.22s ease !important;
            }
            div.stButton > button[kind="primary"]:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 20px rgba(13, 148, 136, 0.38) !important;
            }
            </style>
        """, unsafe_allow_html=True)


inject_custom_styles()


def render_patient_history_view():
    """Renders the patient's personal history of diagnostic tests and PDF downloads (i18n-ready)."""
    user_id = st.session_state.get("user_id")
    records = database.get_user_predictions(user_id)

    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="color: #0D9488; font-weight: 700; margin-bottom: 0.2rem;">
                {i18n.t("history_title")}
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                {i18n.t("history_subtitle")}
            </p>
        </div>
    """, unsafe_allow_html=True)

    if not records:
        st.info(i18n.t("history_empty"))
        return

    for rec in records:
        is_high = "High" in rec["risk_level"] or "Detected" in rec["risk_level"]
        card_border = "#EF4444" if is_high else "#10B981"
        badge_bg = "#FEF2F2" if is_high else "#F0FDF4"
        badge_text = "#991B1B" if is_high else "#166534"

        with st.container():
            st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid {card_border};
                            border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 1.15rem; font-weight: 700; color: #0F172A;">
                                {rec['disease']}
                            </span>
                            <span style="margin-left: 10px; background: {badge_bg}; color: {badge_text}; font-weight: 700;
                                        padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; border: 1px solid {card_border};">
                                {rec['risk_level'].upper()} RISK
                            </span>
                        </div>
                        <span style="color: #64748B; font-size: 0.85rem;">
                            📅 {rec['timestamp'][:16].replace('T', ' ')}
                        </span>
                    </div>
                    <p style="color: #334155; margin: 0.5rem 0 0.8rem 0; font-size: 0.92rem;">
                        <b>{i18n.t("history_eval_label")}</b> {rec['result_text']}
                    </p>
                    <p style="color: #64748B; margin: 0; font-size: 0.85rem;">
                        <b>{i18n.t("history_advice_label")}</b> {rec.get('advice', 'Routine review recommended.')}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            # Re-generate downloadable PDF
            if rec.get("vitals_session_id"):
                v_session = database.get_vitals_session_by_id(rec["vitals_session_id"])
                if v_session:
                    try:
                        in_dict = json.loads(rec["inputs_json"])
                    except Exception:
                        in_dict = {}

                    guidance = recommendations.get_recommendation(rec["disease"], rec["risk_level"])
                    pdf_bytes = pdf_generator.generate_clinical_pdf(
                        patient_name=v_session["patient_name"],
                        patient_id=user_id,
                        age=v_session["age"],
                        gender=v_session["gender"],
                        vitals=v_session,
                        disease_name=rec["disease"],
                        result_title=rec["result_text"],
                        risk_level=rec["risk_level"],
                        confidence_pct=88.5,
                        inputs_dict=in_dict,
                        recommendation=guidance
                    )

                    col_dl1, col_dl2 = st.columns([1, 4])
                    with col_dl1:
                        st.download_button(
                            label=i18n.t("btn_download_pdf"),
                            data=pdf_bytes,
                            file_name=f"Report_{rec['disease'].replace(' ', '_')}_{rec['id']}.pdf",
                            mime="application/pdf",
                            key=f"dl_history_{rec['id']}"
                        )
            st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# ---------------- MAIN APPLICATION CONTROLLER ----------------

def main():
    logged_in = st.session_state.get("logged_in", False)
    role = st.session_state.get("role")
    user_id = st.session_state.get("user_id")

    # 1. Unauthenticated State -> Render Auth Portal
    if not logged_in or not user_id:
        auth.render_auth_page()
        return

    # 2. Authenticated OWNER Flow
    if role == "owner":
        with st.sidebar:
            st.markdown(f"""
                <div style="padding: 0.5rem 0 0.8rem 0;">
                    <h3 style="color: #0D9488; font-weight: 800; margin: 0;">🛡️ Checkup Buddy</h3>
                    <p style="color: #64748B; font-size: 0.85rem; margin: 2px 0 0 0;">{i18n.t("owner_portal")}</p>
                </div>
            """, unsafe_allow_html=True)

            st.write(f"Logged in as: **{st.session_state.get('username')}**")
            st.caption(f"Email: {st.session_state.get('email')}")

            st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

            # Language selector in owner sidebar
            i18n.render_language_selector(key_suffix="owner_sidebar")

            st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
            if st.button(f"🚪 {i18n.t('sign_out')}", use_container_width=True):
                auth.logout_user()

        owner_dashboard.render_owner_dashboard()
        return

    # 3. Authenticated PATIENT Flow
    if role == "patient":
        user_prof = database.get_profile(user_id) or {}
        vitals_unlocked = st.session_state.get("vitals_completed", False) or (st.session_state.get("active_vitals") is not None)

        with st.sidebar:
            st.markdown(f"""
                <div style="padding: 0.5rem 0 0.8rem 0;">
                    <h3 style="color: #0D9488; font-weight: 800; margin: 0;">🩺 Checkup Buddy</h3>
                    <p style="color: #64748B; font-size: 0.85rem; margin: 2px 0 0 0;">{i18n.t("patient_portal")}</p>
                </div>
            """, unsafe_allow_html=True)

            # Display profile pic thumbnail if available
            pic_path = user_prof.get("profile_pic_path")
            full_pic = os.path.join(os.path.dirname(os.path.abspath(__file__)), pic_path) if pic_path else None
            if full_pic and os.path.exists(full_pic):
                st.image(full_pic, width=80)

            display_name = user_prof.get("full_name") or st.session_state.get("username")
            st.write(f"{i18n.t('welcome_user', name=display_name)}")
            st.caption(f"ID: CB-{user_id:06d}")

            st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)

            # Language Selector in Patient Sidebar
            i18n.render_language_selector(key_suffix="patient_sidebar")

            st.markdown("<hr style='margin: 0.8rem 0;'>", unsafe_allow_html=True)

            # Navigation Options
            nav_options = [i18n.t("nav_vitals")]

            if vitals_unlocked:
                nav_options.extend([
                    i18n.t("nav_heart"),
                    i18n.t("nav_diabetes"),
                    i18n.t("nav_parkinsons"),
                    i18n.t("nav_kidney"),
                    i18n.t("nav_liver"),
                    i18n.t("nav_stroke"),
                    i18n.t("nav_breast_cancer"),
                    i18n.t("nav_history"),
                ])
            else:
                nav_options.append(i18n.t("nav_locked"))

            nav_options.append(i18n.t("nav_profile"))

            selected_page = st.radio(
                i18n.t("nav_menu_title"),
                options=nav_options,
                label_visibility="collapsed"
            )

            st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)
            if st.button(f"🚪 {i18n.t('sign_out')}", use_container_width=True):
                auth.logout_user()

        # Page Dispatcher
        vitals_key = i18n.t("nav_vitals")
        locked_key = i18n.t("nav_locked")
        heart_key = i18n.t("nav_heart")
        diabetes_key = i18n.t("nav_diabetes")
        parkinsons_key = i18n.t("nav_parkinsons")
        kidney_key = i18n.t("nav_kidney")
        liver_key = i18n.t("nav_liver")
        stroke_key = i18n.t("nav_stroke")
        breast_key = i18n.t("nav_breast_cancer")
        history_key = i18n.t("nav_history")
        profile_key = i18n.t("nav_profile")

        if selected_page == vitals_key:
            vitals_intake.render_vitals_intake_page()

        elif selected_page == locked_key:
            st.warning(f"🔒 {i18n.t('nav_locked')}")
            st.info(i18n.t("modules_locked_notice"))
            if st.button(i18n.t("btn_proceed_vitals"), type="primary"):
                st.rerun()

        elif selected_page == heart_key:
            vitals_intake.render_vitals_banner()
            heart.render_heart_module()

        elif selected_page == diabetes_key:
            vitals_intake.render_vitals_banner()
            diabetes.render_diabetes_module()

        elif selected_page == parkinsons_key:
            vitals_intake.render_vitals_banner()
            parkinsons.render_parkinsons_module()

        elif selected_page == kidney_key:
            vitals_intake.render_vitals_banner()
            kidney.render_kidney_module()

        elif selected_page == liver_key:
            vitals_intake.render_vitals_banner()
            liver.render_liver_module()

        elif selected_page == stroke_key:
            vitals_intake.render_vitals_banner()
            stroke.render_stroke_module()

        elif selected_page == breast_key:
            vitals_intake.render_vitals_banner()
            breast_cancer.render_breast_cancer_module()

        elif selected_page == history_key:
            render_patient_history_view()

        elif selected_page == profile_key:
            profile.render_profile_page()


if __name__ == "__main__":
    main()
