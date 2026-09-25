"""
Profile management module for Checkup Buddy (v2).
Provides editable demographic profile fields, server-side avatar image compression/resizing,
read-only account verification badges, and profile storage.
"""

import streamlit as st
import os
from PIL import Image
import io

import database
import i18n

PROFILE_PICS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_pics")


def ensure_profile_pics_dir():
    """Ensures profile_pics directory exists on disk."""
    if not os.path.exists(PROFILE_PICS_DIR):
        os.makedirs(PROFILE_PICS_DIR, exist_ok=True)


def process_and_save_avatar(uploaded_file, user_id: int) -> str:
    """
    Compresses and resizes uploaded avatar to a maximum 400x400 JPG,
    saves to disk at profile_pics/{user_id}.jpg, and returns the relative path.
    """
    ensure_profile_pics_dir()
    image = Image.open(uploaded_file)

    # Convert RGBA/P to RGB for clean JPEG saving
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")

    # Resize keeping aspect ratio, max 400x400
    image.thumbnail((400, 400), Image.Resampling.LANCZOS)

    filename = f"{user_id}.jpg"
    dest_path = os.path.join(PROFILE_PICS_DIR, filename)
    image.save(dest_path, "JPEG", quality=85, optimize=True)

    # Return relative path to store in DB
    return os.path.join("profile_pics", filename)


def render_profile_page():
    """Renders the comprehensive profile management page."""
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please sign in to access your profile.")
        return

    profile = database.get_profile(user_id)
    if not profile:
        st.error("Profile not found.")
        return

    st.markdown(f"""
        <div style="margin-bottom: 1.5rem;">
            <h2 style="color: #0D9488; font-weight: 700; margin-bottom: 0.2rem;">{i18n.t("profile_title")}</h2>
            <p style="color: #64748B; font-size: 0.95rem;">{i18n.t("profile_subtitle")}</p>
        </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### Patient Avatar & ID")

        # Display current avatar or fallback
        pic_path = profile.get("profile_pic_path")
        full_pic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), pic_path) if pic_path else None

        if full_pic_path and os.path.exists(full_pic_path):
            st.image(full_pic_path, width=180, caption="Current Profile Photo")
        else:
            # Default avatar placeholder using clean SVG / icon styling
            st.markdown("""
                <div style="width: 150px; height: 150px; border-radius: 50%; background: linear-gradient(135deg, #3B82F6, #1D4ED8);
                            display: flex; align-items: center; justify-content: center; color: white; font-size: 3.5rem;
                            font-weight: bold; margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);">
                    👤
                </div>
            """, unsafe_allow_html=True)

        new_avatar = st.file_uploader(i18n.t("profile_upload_pic"), type=["jpg", "jpeg", "png"])
        if new_avatar is not None:
            if st.button("Update Profile Photo", type="primary"):
                saved_rel_path = process_and_save_avatar(new_avatar, user_id)
                database.update_profile(
                    user_id=user_id,
                    full_name=profile.get("full_name") or profile.get("username"),
                    age=profile.get("age"),
                    gender=profile.get("gender"),
                    date_of_birth=profile.get("date_of_birth"),
                    blood_group=profile.get("blood_group"),
                    address=profile.get("address"),
                    profile_pic_path=saved_rel_path
                )
                st.success("Avatar updated successfully!")
                st.rerun()

        # Patient ID & Account Badges card
        patient_code = f"CB-{user_id:06d}"
        email_verified = profile.get("email_verified") == 1
        mobile_verified = profile.get("mobile_verified") == 1

        # Pre-compute all conditional values BEFORE the f-string to prevent
        # Streamlit from HTML-escaping inline Python ternaries into raw text
        email_color = "#16A34A" if email_verified else "#DC2626"
        email_label = "✓ Email Verified" if email_verified else "✗ Email Pending"
        mobile_color = "#16A34A" if mobile_verified else "#DC2626"
        mobile_label = "✓ Mobile Verified" if mobile_verified else "✗ Mobile Pending"

        st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1.2rem; margin-top: 1.5rem;">
                <p style="font-size: 0.8rem; color: #64748B; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Medical Record ID</p>
                <p style="font-size: 1.3rem; font-weight: 700; color: #1E3A8A; margin: 0 0 1rem 0;">{patient_code}</p>

                <p style="font-size: 0.8rem; color: #64748B; margin: 0; text-transform: uppercase; letter-spacing: 0.5px;">Account Verification</p>
                <div style="display: flex; flex-direction: column; gap: 6px; margin-top: 0.4rem;">
                    <span style="font-size: 0.85rem; color: {email_color}; font-weight: 600;">
                        {email_label}
                    </span>
                    <span style="font-size: 0.85rem; color: {mobile_color}; font-weight: 600;">
                        {mobile_label}
                    </span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown("#### Clinical Demographics")

        with st.form("profile_edit_form"):
            full_name = st.text_input(i18n.t("field_full_name"), value=profile.get("full_name") or profile.get("username") or "")

            col_a, col_b = st.columns(2)
            with col_a:
                age_val = profile.get("age")
                age = st.number_input(i18n.t("field_age"), min_value=1, max_value=120, value=int(age_val) if age_val else 25)

                gender_options = ["Select...", i18n.t("gender_male"), i18n.t("gender_female"), i18n.t("gender_other"), "Prefer not to say"]
                curr_gender = profile.get("gender") or "Select..."
                gender_idx = gender_options.index(curr_gender) if curr_gender in gender_options else 0
                gender = st.selectbox(i18n.t("field_gender"), options=gender_options, index=gender_idx)

            with col_b:
                dob = st.text_input("Date of Birth (YYYY-MM-DD)", value=profile.get("date_of_birth") or "")
                blood_groups = ["Select...", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                curr_bg = profile.get("blood_group") or "Select..."
                bg_idx = blood_groups.index(curr_bg) if curr_bg in blood_groups else 0
                blood_group = st.selectbox(i18n.t("profile_blood_group"), options=blood_groups, index=bg_idx)

            address = st.text_area("Residential Address", value=profile.get("address") or "", height=80)

            # Read-only contact credentials
            st.markdown("##### Account Contact Details (Read-Only)")
            st.text_input(i18n.t("field_email"), value=profile.get("email") or "", disabled=True)
            st.text_input(i18n.t("field_mobile"), value=profile.get("mobile") or "", disabled=True)

            save_btn = st.form_submit_button(i18n.t("btn_save_profile"), type="primary", use_container_width=True)

            if save_btn:
                if not full_name.strip():
                    st.error("Full Name cannot be blank.")
                    return

                selected_gender = None if gender == "Select..." else gender
                selected_bg = None if blood_group == "Select..." else blood_group

                database.update_profile(
                    user_id=user_id,
                    full_name=full_name.strip(),
                    age=int(age),
                    gender=selected_gender,
                    date_of_birth=dob.strip() if dob else None,
                    blood_group=selected_bg,
                    address=address.strip() if address else None,
                    profile_pic_path=profile.get("profile_pic_path")
                )
                st.success(i18n.t("profile_updated"))
                st.rerun()
