"""
Authentication module for Checkup Buddy (v2).
Provides role selection (Patient / Owner), Patient self-service registration
with dual independent OTP verification, and secure PBKDF2 password authentication.
"""

import streamlit as st
import hashlib
import secrets
import os
import re
from datetime import datetime

import database
import otp_service
import i18n

PBKDF2_ITERATIONS = 100_000


def hash_password(password: str, salt_hex: str = None) -> tuple[str, str]:
    """Generates PBKDF2-HMAC-SHA256 hash with 100k iterations and per-user salt."""
    if salt_hex is None:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS
    )
    return derived.hex(), salt_hex


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Verifies a password against the stored PBKDF2 hash and salt."""
    derived, _ = hash_password(password, salt_hex)
    return secrets.compare_digest(derived, stored_hash)
def _get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves a configuration key with priority:
    1. Streamlit secrets: st.secrets[key]
    2. Environment variables: os.getenv(key)
    3. Default value
    Never raises an exception if secrets are absent or Streamlit is uninitialized.
    """
    try:
        import streamlit as st
        if key in st.secrets:
            val = st.secrets[key]
            if val is not None and str(val).strip():
                return str(val).strip()
    except Exception:
        pass

    val = os.getenv(key)
    if val is not None and str(val).strip():
        return str(val).strip()

    return default


def auto_seed_owner_from_env():
    """
    Ensures the owner account configured via Streamlit secrets or environment
    variables exists in the database. Called on startup; safe to run repeatedly (idempotent).
    """
    owner_email = _get_secret("OWNER_EMAIL")
    owner_password = _get_secret("OWNER_PASSWORD")
    owner_username = _get_secret("OWNER_USERNAME", "admin")
    owner_mobile = _get_secret("OWNER_MOBILE", "")

    if not owner_email or not owner_password:
        return

    existing = database.get_user_by_email(owner_email)
    if not existing:
        pwd_hash, salt = hash_password(owner_password)
        database.create_user(
            role="owner",
            username=owner_username,
            email=owner_email,
            mobile=owner_mobile,
            password_hash=pwd_hash,
            salt=salt,
            email_verified=1,
            mobile_verified=1
        )
        print(f"[AUTH] Owner account seeded: {owner_email}")
    elif existing.get("role") == "owner":
        # Keep password in sync with secrets/env if modified
        if not verify_password(owner_password, existing["password_hash"], existing["salt"]):
            pwd_hash, salt = hash_password(owner_password)
            database.update_user_password(existing["id"], pwd_hash, salt)
            print(f"[AUTH] Owner credentials updated from secrets/env: {owner_email}")
    elif existing.get("role") != "owner":
        print(f"[AUTH][WARN] {owner_email} exists with role='{existing.get('role')}' — skipping seed.")




def is_valid_email(email: str) -> bool:
    """Validates email format using regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def is_valid_mobile(mobile: str) -> bool:
    """Validates 10-digit mobile number format."""
    digits = re.sub(r"\D", "", mobile.strip())
    return len(digits) == 10 or (len(digits) == 12 and digits.startswith("91"))


def render_auth_page():
    """Renders the top-level authentication views for Checkup Buddy."""
    auto_seed_owner_from_env()

    # Top language selector bar (visible even before login)
    with st.container():
        col_lang_l, col_lang_c, col_lang_r = st.columns([2, 2, 1])
        with col_lang_r:
            i18n.render_language_selector(key_suffix="auth_top")

    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 2rem; padding-top: 0.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🩺</div>
            <h1 style="font-size: 2.4rem; font-weight: 800;
                       background: linear-gradient(135deg, #0D9488, #1E3A8A);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       margin-bottom: 0.3rem;">
                {i18n.t("app_name")}
            </h1>
            <p style="color: #64748B; font-size: 1.05rem;">
                {i18n.t("app_subtitle")}
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Role Selector
        st.markdown(f"<h4 style='text-align: center; color: #334155; margin-bottom: 1rem;'>{i18n.t('auth_role_prompt')}</h4>", unsafe_allow_html=True)
        role_options = [i18n.t("role_patient"), i18n.t("role_owner")]
        prev_role = st.session_state.get("auth_role", role_options[0])
        default_idx = 1 if prev_role not in [None, "", role_options[0]] else 0
        role_choice = st.radio(
            "Select Your Portal Role",
            options=role_options,
            index=default_idx,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.auth_role = role_choice

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        if role_choice == i18n.t("role_patient"):
            render_patient_auth()
        else:
            render_owner_auth()


def render_owner_auth():
    """Renders login-only interface for Owner/Admin."""
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #F8FAFC, #EFF6FF); border: 1px solid #C7D2FE;
                    border-radius: 14px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem;">
                <span style="font-size: 1.3rem;">🛡️</span>
                <span style="font-weight: 700; color: #1E3A8A; font-size: 1.15rem;">{i18n.t("owner_login_heading")}</span>
            </div>
            <p style="font-size: 0.9rem; color: #64748B; margin: 0;">
                Restricted administrative gateway. Owner accounts are provisioned via server CLI (<code>create_owner.py</code>).
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("owner_login_form"):
        email = st.text_input(i18n.t("field_email"), placeholder="owner@hospital.com").strip()
        password = st.text_input(i18n.t("field_password"), type="password", placeholder="••••••••")
        submitted = st.form_submit_button(i18n.t("btn_signin"), use_container_width=True, type="primary")

        if submitted:
            if not email or not password:
                st.error(i18n.t("enter_valid_email"))
                return

            user = database.get_user_by_email(email)
            if not user or user["role"] != "owner":
                st.error(i18n.t("invalid_credentials"))
                return

            if verify_password(password, user["password_hash"], user["salt"]):
                st.session_state.user_id = user["id"]
                st.session_state.role = "owner"
                st.session_state.username = user["username"]
                st.session_state.email = user["email"]
                st.session_state.logged_in = True
                st.success(i18n.t("auth_success"))
                st.rerun()
            else:
                st.error(i18n.t("invalid_credentials"))


def render_patient_auth():
    """Renders Patient Login or Dual-OTP Signup tabs."""
    tab_login, tab_signup = st.tabs([i18n.t("tab_signin"), i18n.t("tab_register")])

    with tab_login:
        st.markdown(f"<p style='color: #0D9488; font-weight: 600;'>{i18n.t('patient_login_heading')}</p>", unsafe_allow_html=True)
        with st.form("patient_login_form"):
            email_or_username = st.text_input(i18n.t("field_username_email"), placeholder="e.g. john@example.com").strip()
            password = st.text_input(i18n.t("field_password"), type="password", placeholder="••••••••")
            login_btn = st.form_submit_button(i18n.t("btn_signin"), use_container_width=True, type="primary")

            if login_btn:
                if not email_or_username or not password:
                    st.error(i18n.t("invalid_credentials"))
                    return

                user = database.get_user_by_email(email_or_username)
                if not user:
                    user = database.get_user_by_username(email_or_username)

                if not user or user["role"] != "patient":
                    st.error(i18n.t("invalid_credentials"))
                    return

                if verify_password(password, user["password_hash"], user["salt"]):
                    st.session_state.user_id = user["id"]
                    st.session_state.role = "patient"
                    st.session_state.username = user["username"]
                    st.session_state.email = user["email"]
                    st.session_state.logged_in = True
                    st.success(i18n.t("auth_success"))
                    st.rerun()
                else:
                    st.error(i18n.t("invalid_credentials"))

    with tab_signup:
        render_patient_signup_flow()


def render_patient_signup_flow():
    """
    Renders a unified Patient Sign Up form with Email OTP verification,
    real-time validations, and gated submission.
    """
    # Initialize session states for email OTP signup flow
    if "su_email_verified" not in st.session_state:
        st.session_state.su_email_verified = False
    if "su_verified_email" not in st.session_state:
        st.session_state.su_verified_email = ""
    if "su_email_otp_sent" not in st.session_state:
        st.session_state.su_email_otp_sent = False
    if "su_pending_email" not in st.session_state:
        st.session_state.su_pending_email = ""

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #F0FDFA, #EFF6FF); border: 1px solid #99F6E4;
                    border-radius: 12px; padding: 1.1rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.25rem;">
                <span style="font-size: 1.2rem;">✨</span>
                <span style="font-weight: 700; color: #0F766E; font-size: 1.1rem;">{i18n.t("signup_heading")}</span>
            </div>
            <p style="font-size: 0.88rem; color: #64748B; margin: 0;">
                {i18n.t("signup_subheading")}
            </p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Username field
    username = st.text_input(
        f"{i18n.t('field_username')} *",
        placeholder="e.g. john_doe24",
        key="su_field_username"
    ).strip()

    username_valid = False
    if username:
        if len(username) < 3:
            st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem; margin: -8px 0 10px 0;'>⚠️ {i18n.t('error_username_invalid')}</p>", unsafe_allow_html=True)
        elif database.get_user_by_username(username):
            st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem; margin: -8px 0 10px 0;'>⚠️ {i18n.t('error_username_taken')}</p>", unsafe_allow_html=True)
        else:
            username_valid = True
            st.markdown("<p style='color: #10B981; font-size: 0.82rem; margin: -8px 0 10px 0;'>✓ Username is available</p>", unsafe_allow_html=True)

    # 2. Email field with independent OTP verification
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    if st.session_state.su_email_verified:
        col_e1, col_e2 = st.columns([3, 1.2])
        with col_e1:
            st.text_input(
                f"{i18n.t('field_email')} *",
                value=st.session_state.su_verified_email,
                disabled=True,
                key="su_email_verified_disp"
            )
        with col_e2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background: #DCFCE7; color: #166534; font-weight: 700;
                            padding: 8px 10px; border-radius: 8px; border: 1px solid #86EFAC;
                            text-align: center; font-size: 0.85rem;">
                    ✅ {i18n.t("otp_verified_badge")}
                </div>
            """, unsafe_allow_html=True)
        st.markdown("<p style='color: #10B981; font-size: 0.85rem; font-weight: 600; margin-top: -6px;'>✓ Email verified successfully</p>", unsafe_allow_html=True)
        if st.button("Change Email", key="btn_change_verified_email", type="secondary"):
            st.session_state.su_email_verified = False
            st.session_state.su_verified_email = ""
            st.session_state.su_email_otp_sent = False
            st.rerun()
    else:
        col_e_in, col_e_btn = st.columns([3, 1.2])
        with col_e_in:
            email_val = st.text_input(
                f"{i18n.t('field_email')} *",
                placeholder="john@example.com",
                key="su_field_email"
            ).strip()
        with col_e_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            send_email_clicked = st.button(i18n.t("btn_send_otp"), key="btn_send_e_otp", use_container_width=True)

        if send_email_clicked:
            if not email_val or not is_valid_email(email_val):
                st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem;'>⚠️ {i18n.t('error_email_invalid')}</p>", unsafe_allow_html=True)
            elif database.get_user_by_email(email_val):
                st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem;'>⚠️ {i18n.t('error_email_taken')}</p>", unsafe_allow_html=True)
            else:
                ok, msg = otp_service.dispatch_single_otp(email_val, "email")
                if not ok:
                    st.markdown(f"<p style='color: #D97706; font-size: 0.82rem;'>⏳ {msg}</p>", unsafe_allow_html=True)
                else:
                    st.session_state.su_email_otp_sent = True
                    st.session_state.su_pending_email = email_val
                    st.rerun()

        if st.session_state.su_email_otp_sent:
            target_e = st.session_state.get("su_pending_email") or email_val

            st.markdown(f"""
                <div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 8px;
                            padding: 0.65rem 0.9rem; margin: 0.4rem 0 0.6rem 0;">
                    <span style="color: #166534; font-size: 0.85rem; font-weight: 600;">
                        📨 Verification code sent to <code>{target_e}</code>. Please check your inbox (and spam folder).
                    </span>
                </div>
            """, unsafe_allow_html=True)

            col_eo1, col_eo2 = st.columns([2.5, 1])
            with col_eo1:
                e_code = st.text_input("Enter OTP", max_chars=6, key="su_email_otp_code_in", placeholder="Enter 6-digit OTP")
            with col_eo2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                verify_e_clicked = st.button(i18n.t("btn_verify_otp"), key="btn_do_verify_email_otp", use_container_width=True, type="primary")

            if verify_e_clicked:
                code_to_check = e_code.strip() or st.session_state.get("su_email_otp_code_in", "").strip()
                ok, msg = otp_service.verify_otp_token(target_e, "email", code_to_check)
                if ok:
                    st.session_state.su_email_verified = True
                    st.session_state.su_verified_email = target_e
                    st.session_state.su_email_otp_sent = False
                    st.rerun()
                else:
                    st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem;'>❌ {msg}</p>", unsafe_allow_html=True)

    # 3. Mobile Number field (Optional plain field, no OTP verification)
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    mobile_val = st.text_input(
        f"{i18n.t('field_mobile')} (Optional)",
        placeholder="e.g. 9876543210",
        key="su_field_mobile"
    ).strip()

    # 4. Age and Gender row
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    col_age, col_gender = st.columns(2)
    with col_age:
        age = st.number_input(
            f"{i18n.t('field_age')} *",
            min_value=1,
            max_value=120,
            value=25,
            step=1,
            key="su_field_age"
        )
        age_valid = bool(1 <= age <= 120)

    with col_gender:
        gender_labels = {
            "Male": i18n.t("gender_male"),
            "Female": i18n.t("gender_female"),
            "Other": i18n.t("gender_other"),
            "Prefer not to say": i18n.t("gender_prefer_not_to_say")
        }
        gender = st.selectbox(
            f"{i18n.t('field_gender')} *",
            options=list(gender_labels.keys()),
            format_func=lambda x: gender_labels.get(x, x),
            key="su_field_gender"
        )
        gender_valid = bool(gender)

    # 5. Password & Confirm Password row
    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pwd = st.text_input(
            f"{i18n.t('field_password')} *",
            type="password",
            placeholder="••••••••",
            key="su_field_password"
        )
    with col_p2:
        confirm_pwd = st.text_input(
            f"{i18n.t('field_confirm_password')} *",
            type="password",
            placeholder="••••••••",
            key="su_field_confirm_pwd"
        )

    pwd_valid = False
    if pwd or confirm_pwd:
        if len(pwd) < 6:
            st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem; margin: -8px 0 10px 0;'>⚠️ {i18n.t('error_password_length')}</p>", unsafe_allow_html=True)
        elif pwd != confirm_pwd:
            st.markdown(f"<p style='color: #EF4444; font-size: 0.82rem; margin: -8px 0 10px 0;'>⚠️ {i18n.t('passwords_dont_match')}</p>", unsafe_allow_html=True)
        else:
            pwd_valid = True
            st.markdown("<p style='color: #10B981; font-size: 0.82rem; margin: -8px 0 10px 0;'>✓ Passwords match</p>", unsafe_allow_html=True)

    # 6. Gated submission check: Email verified and required fields (username, email, age, gender, password) filled
    email_ok = bool(st.session_state.su_email_verified and st.session_state.su_verified_email)
    can_submit = bool(username_valid and email_ok and age_valid and gender_valid and pwd_valid)

    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

    # Pending steps helper
    if not can_submit:
        pending_list = []
        if not username_valid:
            pending_list.append(i18n.t("field_username"))
        if not email_ok:
            pending_list.append(f"{i18n.t('field_email')} (OTP)")
        if not age_valid:
            pending_list.append(i18n.t("field_age"))
        if not gender_valid:
            pending_list.append(i18n.t("field_gender"))
        if not pwd_valid:
            pending_list.append(i18n.t("field_password"))

        badges = " ".join([f"<span style='background: #F1F5F9; color: #475569; padding: 2px 8px; border-radius: 6px; font-size: 0.78rem; border: 1px solid #CBD5E1;'>⏳ {item}</span>" for item in pending_list])
        st.markdown(f"""
            <div style="background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px;
                        padding: 0.6rem 0.9rem; margin-bottom: 0.8rem;">
                <span style="font-size: 0.82rem; color: #64748B;">Pending before creation:</span> {badges}
            </div>
        """, unsafe_allow_html=True)

    create_account_btn = st.button(
        f"✨ {i18n.t('btn_create_account')}",
        key="btn_create_patient_account",
        type="primary",
        use_container_width=True,
        disabled=not can_submit
    )

    if create_account_btn and can_submit:
        verified_email = st.session_state.su_verified_email
        clean_mobile = re.sub(r"\D", "", mobile_val) if mobile_val else ""
        pwd_hash, salt = hash_password(pwd)

        new_uid = database.create_user(
            role="patient",
            username=username,
            email=verified_email,
            mobile=clean_mobile,
            password_hash=pwd_hash,
            salt=salt,
            email_verified=1,
            mobile_verified=1 if clean_mobile else 0
        )
        database.update_profile(
            user_id=new_uid,
            full_name=username,
            age=int(age),
            gender=gender,
            date_of_birth=None,
            blood_group=None,
            address=None
        )

        # Clean up temporary signup session states
        for key in [
            "su_email_verified", "su_verified_email", "su_email_otp_sent", "su_pending_email",
            "su_email_demo_code", "su_field_username", "su_field_email", "su_field_mobile",
            "su_field_password", "su_field_confirm_pwd", "su_field_age", "su_field_gender",
            "su_email_otp_code_in", "auth_role"  # clear auth tab state too
        ]:
            st.session_state.pop(key, None)

        # Set session and log in
        st.session_state.user_id = new_uid
        st.session_state.role = "patient"
        st.session_state.username = username
        st.session_state.email = verified_email
        st.session_state.logged_in = True
        st.session_state.signup_just_completed = True  # triggers welcome screen on first load
        st.rerun()



def logout_user():
    """Clears user session and logs out."""
    for key in ["user_id", "role", "username", "email", "logged_in", "active_vitals"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
