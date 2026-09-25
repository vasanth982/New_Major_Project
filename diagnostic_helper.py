"""
Diagnostic Helper Module for Checkup Buddy (v2).
Provides standardized X-ray/medical imaging file uploaders across all 7 disease modules
and automated clinical diagnosis email dispatch with attached hospital-grade PDF reports.
"""

import streamlit as st
from PIL import Image as PILImage
import database
import otp_service


def render_xray_uploader(disease_name: str, key_suffix: str, modality: str = "X-ray Image"):
    """
    Renders an optional X-ray / medical image file uploader with instant image preview
    and a clear 'Image received — analysis model coming soon' placeholder card.
    Does not block existing symptoms or vitals-based diagnostic workflows.
    """
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #EFF6FF, #F0FDF4); border: 1.5px solid #BFDBFE;
                    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.4rem;">
                <span style="font-size: 1.3rem;">🩻</span>
                <span style="font-weight: 700; color: #1E40AF; font-size: 1rem;">Upload {disease_name} {modality} (Optional)</span>
            </div>
            <p style="font-size: 0.85rem; color: #64748B; margin: 0;">
                Upload an X-ray or medical imaging scan for visual reference. AI-assisted radiological imaging analysis is currently in development.
            </p>
        </div>
    """, unsafe_allow_html=True)

    xray_file = st.file_uploader(
        f"📤 Upload {disease_name} {modality}",
        type=["jpg", "jpeg", "png"],
        key=f"{key_suffix}_xray_upload",
        help="Accepted formats: JPG, JPEG, PNG. Maximum 10MB."
    )

    if xray_file is not None:
        col_img, col_note = st.columns([1, 1.5])
        with col_img:
            uploaded_img = PILImage.open(xray_file)
            st.image(uploaded_img, caption=f"Uploaded: {xray_file.name}", use_container_width=True)
        with col_note:
            st.markdown(f"""
                <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 10px;
                            padding: 1rem 1.2rem; margin-top: 0.5rem;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #92400E; margin-bottom: 0.4rem;">
                        🔬 Image Received — Analysis Model Coming Soon
                    </div>
                    <p style="font-size: 0.85rem; color: #78350F; margin: 0;">
                        Your {disease_name} imaging scan (<b>{xray_file.name}</b>) has been received and previewed successfully.
                        Deep-learning radiological image evaluation is under active development. You may proceed with the clinical risk assessment below without interruption.
                    </p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    return xray_file


def auto_send_diagnosis_email(
    user_id: int,
    vitals: dict,
    disease_name: str,
    disease_key: str,
    record_id: int,
    result_title: str,
    risk_level: str,
    confidence_pct: float,
    pdf_bytes: bytes
) -> None:
    """
    Automatically sends the diagnosis summary and attached PDF report to the user's
    verified registered email address. Shows a confirmation message in the app UI.
    Wrapped in try/except so email delivery errors never block or crash the diagnostic flow.
    """
    try:
        user_email = st.session_state.get("email")
        if not user_email and user_id:
            user_record = database.get_user_by_id(user_id)
            if user_record:
                user_email = user_record.get("email")

        if user_email:
            email_state_key = f"emailed_{disease_key}_{record_id}"
            if email_state_key not in st.session_state:
                sent, msg = otp_service.send_diagnosis_report_email(
                    to_email=user_email,
                    patient_name=vitals.get("patient_name", "Patient") if vitals else "Patient",
                    disease_name=disease_name,
                    result_title=result_title,
                    risk_level=risk_level,
                    confidence_pct=confidence_pct,
                    pdf_bytes=pdf_bytes
                )
                st.session_state[email_state_key] = (sent, msg)

            cached_result = st.session_state.get(email_state_key)
            if cached_result and cached_result[0]:
                st.success(f"📧 Result emailed to your registered email address ({user_email}).")
    except Exception as e:
        print(f"[Auto-email warning for {disease_name}]: {e}")
