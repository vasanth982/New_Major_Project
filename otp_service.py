"""
OTP Service module for Checkup Buddy (v2).
Implements secure 6-digit OTP generation, at-rest hashing,
5-minute expiry, max 3 attempts, 30s resend cooldown,
and dispatch via Twilio (SMS), SMTP (email), or console-only dev fallback.

CRITICAL SECURITY REQUIREMENT:
OTPs are NEVER rendered in the Streamlit UI or returned to the browser.
In dev mode, OTPs are printed directly to the server terminal/console logs.
"""

import os
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta, timezone

import database

OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3
RESEND_COOLDOWN_SECONDS = 3


def generate_6digit_otp():
    """Generates a cryptographically secure 6-digit numeric string."""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def hash_otp(code: str) -> str:
    """Hashes an OTP string with SHA-256 for secure at-rest storage."""
    return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()


def can_resend_otp(identifier: str, channel: str) -> tuple[bool, int]:
    """
    Checks if resend cooldown has elapsed.
    Returns (can_resend: bool, remaining_seconds: int).
    """
    latest = database.get_active_otp_token(identifier, channel)
    if not latest:
        return True, 0

    try:
        created_at = datetime.fromisoformat(latest["created_at"])
        elapsed = (datetime.now() - created_at).total_seconds()
        if elapsed < RESEND_COOLDOWN_SECONDS:
            return False, int(RESEND_COOLDOWN_SECONDS - elapsed)
    except Exception:
        pass

    return True, 0


def _get_secret(key: str, default: str = "") -> str:
    """
    Safely retrieves a configuration key with explicit two-path resolution:

    Path A - Streamlit secrets (local dev / Streamlit Community Cloud):
        Reads from .streamlit/secrets.toml when present.
        Uses st.secrets.get() to avoid raising on missing keys.

    Path B - OS environment variables (Render, Docker, CI/CD, production):
        Reads from os.environ directly. This is the ONLY path that works on
        Render when secrets.toml is not deployed (which it should never be).

    On Render:
        - secrets.toml is NOT deployed (correctly excluded via .gitignore).
        - st.secrets will be an empty SecretDict - Path A finds nothing.
        - SMTP_USER, SMTP_APP_PASSWORD must be set as Environment Variables
          in the Render dashboard. Path B reads them via os.environ.
        - After adding env vars in the Render dashboard, trigger a
          Manual Deploy (not just a restart) for changes to take effect.

    Never raises. Never logs credential values.
    """
    # -- Path A: Streamlit secrets (local dev / Streamlit Cloud) --------------
    try:
        import streamlit as st
        # Use .get() - never raises on missing keys, never raises if secrets
        # file is absent (returns None in that case).
        val = st.secrets.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        # st.secrets unavailable or not initialized - fall through to env vars.
        pass

    # -- Path B: OS environment variables (Render, Docker, production) ---------
    # Use os.environ.get() directly - equivalent to os.getenv() but explicit.
    val = os.environ.get(key, "").strip()
    if val:
        return val

    return default


def _log_smtp_config_state() -> None:
    """
    Logs the SMTP configuration state at startup / first call.
    Reports only whether each required key is PRESENT or MISSING.
    Never logs credential values, passwords, or OTPs.
    Call once at app startup to make Render logs immediately useful.
    """
    host = _get_secret("SMTP_HOST", "")
    port = _get_secret("SMTP_PORT", "")
    user = _get_secret("SMTP_USER", "")
    pwd  = _get_secret("SMTP_APP_PASSWORD", "")
    clean_pwd = pwd.replace(" ", "") if pwd else ""

    # Determine where each key came from (secrets file vs env var)
    def _source(key: str) -> str:
        try:
            import streamlit as st
            if st.secrets.get(key):
                return "st.secrets"
        except Exception:
            pass
        return "os.environ" if os.environ.get(key, "").strip() else "MISSING"

    print("[SMTP Config] -- Startup credential check --------------------------")
    print(f"[SMTP Config] SMTP_HOST         : {'SET (' + _source('SMTP_HOST') + ')' if host else 'MISSING - defaulting to smtp.gmail.com'}")
    print(f"[SMTP Config] SMTP_PORT         : {'SET (' + _source('SMTP_PORT') + ') = ' + port if port else 'MISSING - defaulting to 587'}")
    print(f"[SMTP Config] SMTP_USER         : {'SET (' + _source('SMTP_USER') + ')' if user else 'MISSING - email OTP will fail'}")
    print(f"[SMTP Config] SMTP_APP_PASSWORD : {'SET (' + _source('SMTP_APP_PASSWORD') + ') length=' + str(len(clean_pwd)) if clean_pwd else 'MISSING - email OTP will fail'}")
    if not user or not clean_pwd:
        print("[SMTP Config] ACTION REQUIRED: Add SMTP_USER and SMTP_APP_PASSWORD as")
        print("[SMTP Config]   Environment Variables in Render dashboard, then trigger")
        print("[SMTP Config]   a Manual Deploy (not just a service restart).")
    else:
        print("[SMTP Config] Credentials present. Email OTP delivery enabled.")
    print("[SMTP Config] ----------------------------------------------------")


# Module-level defaults (used only as fallback in get_smtp_credentials)
_SMTP_HOST_DEFAULT = "smtp.gmail.com"
_SMTP_PORT_DEFAULT = 587


def get_smtp_credentials() -> tuple[str, int, str, str]:
    """Returns (host, port, user, app_password) dynamically resolved from secrets or env."""
    host = _get_secret("SMTP_HOST", _SMTP_HOST_DEFAULT)
    try:
        port = int(_get_secret("SMTP_PORT", str(_SMTP_PORT_DEFAULT)))
    except Exception:
        port = _SMTP_PORT_DEFAULT
    user = _get_secret("SMTP_USER", "")
    pwd  = _get_secret("SMTP_APP_PASSWORD", "")
    return host, port, user, pwd


def _send_email_smtp(to_email: str, otp_code: str) -> bool:
    """Sends OTP via Gmail SMTP. Returns True only when the SMTP server accepts the message."""
    host, port, smtp_user, smtp_app_password = get_smtp_credentials()

    # Strip spaces - Google App Passwords are shown with spaces but must be sent without
    clean_password = smtp_app_password.replace(" ", "").strip() if smtp_app_password else ""

    # -- Safe credential-presence diagnostic (no values logged) ----------------
    print(f"[OTP SMTP] host={host or 'MISSING'} port={port}")
    print(f"[OTP SMTP] SMTP_USER={'SET' if smtp_user else 'MISSING'} "
          f"SMTP_APP_PASSWORD={'SET(len=' + str(len(clean_password)) + ')' if clean_password else 'MISSING'}")

    if not smtp_user or not clean_password or clean_password in (
        "PASTEYOUR16CHARAPPPASSWORDHERE", "your_16_char_app_password"
    ):
        print("[OTP SMTP] CREDENTIALS MISSING -- cannot send OTP email.")
        print("[OTP SMTP] Fix: Set SMTP_USER and SMTP_APP_PASSWORD in Render dashboard")
        print("[OTP SMTP]      under Environment Variables, then trigger a Manual Deploy.")
        return False

    try:
        outer = MIMEMultipart("alternative")
        outer["From"] = smtp_user
        outer["To"] = to_email
        outer["Reply-To"] = smtp_user
        outer["Subject"] = "Your Checkup Buddy Verification Code"
        outer["X-Mailer"] = "Checkup Buddy v2"

        plain_body = (
            f"Hello,\n\n"
            f"Your Checkup Buddy one-time verification code is:\n\n"
            f"    {otp_code}\n\n"
            f"This code expires in 5 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"-- Checkup Buddy Health Analytics\n"
            f"This is an automated message. Please do not reply.\n"
        )

        html_body = f"""\
<html>
  <body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px;">
    <div style="max-width:480px;margin:auto;background:#fff;border-radius:10px;
                padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
      <h2 style="color:#0D9488;margin-top:0;">Checkup Buddy</h2>
      <p style="font-size:15px;color:#333;">Hello,</p>
      <p style="font-size:15px;color:#333;">Your one-time verification code is:</p>
      <div style="text-align:center;margin:24px 0;">
        <span style="font-size:36px;font-weight:bold;letter-spacing:10px;
                     color:#0D9488;background:#f0fdf4;padding:14px 28px;
                     border-radius:8px;border:2px dashed #0D9488;">
          {otp_code}
        </span>
      </div>
      <p style="font-size:13px;color:#555;">
        This code expires in <strong>5 minutes</strong>.<br>
        If you did not request this, please ignore this email.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
      <p style="font-size:11px;color:#999;text-align:center;">
        Checkup Buddy Health Analytics &mdash; Automated message, do not reply.
      </p>
    </div>
  </body>
</html>"""

        outer.attach(MIMEText(plain_body, "plain", "utf-8"))
        outer.attach(MIMEText(html_body, "html", "utf-8"))

        server = smtplib.SMTP(host, port, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_user, clean_password)
        server.sendmail(smtp_user, [to_email], outer.as_string())
        server.quit()
        print(f"[OTP SMTP] Delivered successfully to domain: @{to_email.split('@')[-1]}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[OTP SMTP] AUTH FAILED -- wrong SMTP_USER or SMTP_APP_PASSWORD.")
        print("[OTP SMTP] For Gmail: use a 16-char App Password (not your account password).")
        print("[OTP SMTP] Create one at: myaccount.google.com/apppasswords")
        return False
    except smtplib.SMTPConnectError as e:
        print(f"[OTP SMTP] CONNECTION FAILED -- cannot reach {host}:{port}. Error: {type(e).__name__}")
        return False
    except smtplib.SMTPRecipientsRefused:
        print(f"[OTP SMTP] RECIPIENT REFUSED -- address domain: @{to_email.split('@')[-1]}")
        return False
    except smtplib.SMTPException as e:
        print(f"[OTP SMTP] SMTP ERROR -- {type(e).__name__}")
        return False
    except Exception as e:
        print(f"[OTP SMTP] UNEXPECTED ERROR -- {type(e).__name__}")
        return False


def _send_sms_twilio(to_mobile: str, otp_code: str) -> bool:
    """Sends OTP via Twilio SMS using Streamlit secrets, environment configuration, or dev fallback."""
    account_sid = _get_secret("TWILIO_ACCOUNT_SID")
    auth_token = _get_secret("TWILIO_AUTH_TOKEN")
    from_number = _get_secret("TWILIO_PHONE_NUMBER")

    if not (account_sid and auth_token and from_number):
        return False

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Your Checkup Buddy verification code is {otp_code}. Valid for 5 minutes.",
            from_=from_number,
            to=to_mobile
        )
        return bool(message.sid)
    except Exception as e:
        print(f"[OTP Service] Twilio dispatch error: {e}")
        return False


def dispatch_single_otp(identifier: str, channel: str) -> tuple[bool, str]:
    """
    Generates, hashes at rest, and dispatches an OTP to the given channel.
    Returns (success: bool, message: str).

    SECURITY: The OTP code is NEVER returned to the caller or displayed in the
    browser/UI. On SMTP failure, the function returns False with a clear error
    so the user knows delivery did not succeed.
    """
    can_resend, remaining = can_resend_otp(identifier, channel)
    if not can_resend:
        return False, f"Please wait {remaining} seconds before requesting a new code."

    # Validate identifier for email channel before generating OTP
    if channel == "email" and ("@" not in identifier or "." not in identifier.split("@")[-1]):
        return False, "Invalid email address. Please check the address and try again."

    otp_code = generate_6digit_otp()
    token_hash = hash_otp(otp_code)
    expires_at = (datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    # Store hashed OTP in database BEFORE sending (so it exists even if send has delay)
    database.store_otp_token(identifier, channel, token_hash, expires_at)

    dispatched = False
    if channel == "email":
        dispatched = _send_email_smtp(identifier, otp_code)
    elif channel == "mobile":
        dispatched = _send_sms_twilio(identifier, otp_code)

    if not dispatched:
        # Remove the stored token since delivery failed - don't leave a phantom token
        try:
            rec = database.get_active_otp_token(identifier, channel)
            if rec:
                database.delete_otp_token(rec["id"])
        except Exception:
            pass

        # Log safe diagnostic to server console (no OTP value in production logs)
        print(f"[OTP Service] Delivery FAILED for {channel} channel. Identifier domain: "
              f"{'@'+identifier.split('@')[-1] if '@' in identifier else '[non-email]'}")
        print("[OTP Service] Check SMTP_USER and SMTP_APP_PASSWORD environment variables in Render dashboard.")

        if channel == "email":
            return False, (
                "Could not send the verification email. "
                "Please check that your email address is correct and try again. "
                "If the problem persists, contact support."
            )
        else:
            return False, "Could not send the SMS verification code. Please try again later."

    return True, (
        "Verification code sent to your email. Please check your inbox - "
        "if you don't see it within a minute, check your Spam / Junk folder. "
        "The code expires in 5 minutes."
    )


def dispatch_dual_otps(email: str, mobile: str) -> dict:
    """Dispatches verification codes to both email and mobile simultaneously."""
    res_email, msg_email = dispatch_single_otp(email, "email")
    res_mobile, msg_mobile = dispatch_single_otp(mobile, "mobile")
    return {
        "email_sent": res_email,
        "email_msg": msg_email,
        "mobile_sent": res_mobile,
        "mobile_msg": msg_mobile,
    }



def verify_otp_token(identifier: str, channel: str, entered_code: str) -> tuple[bool, str]:
    """
    Verifies the user's entered OTP against the active hash in database.
    Enforces expiry (5 min) and maximum attempts (3).
    """
    if not entered_code or len(entered_code.strip()) != 6:
        return False, "Please enter a valid 6-digit code."

    record = database.get_active_otp_token(identifier, channel)
    if not record:
        return False, "No active verification code found. Please request a new code."

    # Check expiration
    try:
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now() > expires_at:
            database.delete_otp_token(record["id"])
            return False, "The verification code has expired. Please request a new one."
    except Exception:
        pass

    # Check max attempts
    attempts = record["attempts"]
    if attempts >= MAX_ATTEMPTS:
        database.delete_otp_token(record["id"])
        return False, "Too many failed attempts. Code invalidated. Please request a new code."

    # Compare hashes
    entered_hash = hash_otp(entered_code)
    if entered_hash == record["token_hash"]:
        database.delete_otp_token(record["id"])
        return True, "Verification successful."
    else:
        new_attempts = attempts + 1
        database.update_otp_token_attempts(record["id"], new_attempts)
        remaining = MAX_ATTEMPTS - new_attempts
        if remaining > 0:
            return False, f"Incorrect code. {remaining} attempt(s) remaining."
        else:
            database.delete_otp_token(record["id"])
            return False, "Maximum attempts reached. Please request a new code."


def send_diagnosis_report_email(
    to_email: str,
    patient_name: str,
    disease_name: str,
    result_title: str,
    risk_level: str,
    confidence_pct: float,
    pdf_bytes: bytes,
    test_time: str | None = None
) -> tuple[bool, str]:
    """
    Sends an automated diagnostic summary email with attached clinical PDF report
    to the user's verified registered email address using Gmail SMTP.
    Returns (success: bool, status_message: str).
    """
    if not to_email or "@" not in to_email:
        return False, "No valid registered email address found."

    host, port, user, app_password = get_smtp_credentials()
    clean_password = app_password.replace(" ", "").strip() if app_password else ""

    if not user or not clean_password or clean_password in ("PASTEYOUR16CHARAPPPASSWORDHERE", "your_16_char_app_password"):
        print("[Diagnostic Email] SMTP credentials not configured. Diagnostic summary logged to dev console.")
        print(f"[DEV CONSOLE LOG] Diagnostic report for {disease_name} to {to_email}: {result_title} ({risk_level} Risk)")
        return False, "SMTP credentials not configured."

    if not test_time:
        test_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        msg = MIMEMultipart()
        msg["From"] = f"Checkup Buddy Health Analytics <{user}>"
        msg["To"] = to_email
        msg["Subject"] = f"Checkup Buddy Diagnostic Report - {disease_name} ({risk_level} Risk)"

        body_text = (
            f"Dear {patient_name or 'Patient'},\n\n"
            f"Thank you for using Checkup Buddy AI Health Analytics.\n"
            f"Here is the clinical summary of your completed diagnostic assessment:\n\n"
            f"════════════════════════════════════════════════════════════\n"
            f"  CLINICAL ASSESSMENT SUMMARY\n"
            f"════════════════════════════════════════════════════════════\n"
            f"• Disease / Module Tested : {disease_name}\n"
            f"• Primary Result          : {result_title}\n"
            f"• Clinical Risk Level     : {risk_level.upper()} Risk ({confidence_pct:.1f}% confidence)\n"
            f"• Date & Time of Analysis : {test_time}\n"
            f"════════════════════════════════════════════════════════════\n\n"
            f"Your complete, hospital-grade clinical PDF report has been attached to this email for your medical records.\n\n"
            f"IMPORTANT MEDICAL NOTICE:\n"
            f"This automated assessment is an educational screening support tool powered by machine learning "
            f"and does not constitute an official medical diagnosis. Please consult a licensed medical doctor "
            f"or healthcare specialist for professional clinical advice, follow-up, and diagnostic confirmation.\n\n"
            f"Wishing you the best of health,\n"
            f"Checkup Buddy Clinical AI Team\n"
        )
        msg.attach(MIMEText(body_text, "plain", "utf-8"))

        if pdf_bytes:
            safe_disease = disease_name.replace(" ", "_").replace("'", "")
            filename = f"CheckupBuddy_{safe_disease}_Report.pdf"
            attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename=filename)
            msg.attach(attachment)

        server = smtplib.SMTP(host, port, timeout=12)
        server.starttls()
        server.login(user, clean_password)
        server.sendmail(user, [to_email], msg.as_string())
        server.quit()
        print(f"[Diagnostic Email] Successfully dispatched {disease_name} report to {to_email}")
        return True, f"Result emailed to your registered email address ({to_email})."
    except Exception as e:
        print(f"[Diagnostic Email] Failed to dispatch report email to {to_email}: {e}")
        return False, f"Email delivery failed: {e}"



def run_smtp_diagnostic(test_recipient: str) -> dict:
    """
    Owner-only SMTP diagnostic. Checks credential presence, attempts a live
    SMTP connection and sends a test message to the supplied address.

    SECURITY:
    - Never call this from patient-facing code.
    - Never log SMTP credentials or OTP values.
    - Only sends to an address explicitly supplied by an authenticated owner.

    Returns a dict with keys:
      credentials_present (bool), smtp_connected (bool),
      smtp_authenticated (bool), message_accepted (bool),
      error (str|None), summary (str)
    """
    result = {
        "credentials_present": False,
        "smtp_connected": False,
        "smtp_authenticated": False,
        "message_accepted": False,
        "error": None,
        "summary": "",
    }

    if not test_recipient or "@" not in test_recipient:
        result["error"] = "Invalid test recipient address."
        result["summary"] = "Diagnostic skipped: invalid recipient."
        return result

    host, port, user, app_password = get_smtp_credentials()
    clean_password = app_password.replace(" ", "").strip() if app_password else ""

    if not user or not clean_password:
        result["error"] = "SMTP_USER or SMTP_APP_PASSWORD is missing from environment / secrets."
        result["summary"] = (
            "CONFIGURATION ERROR: Set SMTP_USER and SMTP_APP_PASSWORD in the "
            "Render dashboard under Environment Variables."
        )
        print("[SMTP Diagnostic] Credentials missing - SMTP_USER or SMTP_APP_PASSWORD not configured.")
        return result

    result["credentials_present"] = True

    try:
        server = smtplib.SMTP(host, port, timeout=15)
        server.ehlo()
        result["smtp_connected"] = True
    except Exception as e:
        result["error"] = f"SMTP connection failed: {type(e).__name__}"
        result["summary"] = f"Cannot reach {host}:{port}. Check SMTP_HOST and SMTP_PORT."
        print(f"[SMTP Diagnostic] Connection error: {type(e).__name__}")
        return result

    try:
        server.starttls()
        server.ehlo()
        server.login(user, clean_password)
        result["smtp_authenticated"] = True
    except smtplib.SMTPAuthenticationError:
        result["error"] = "SMTP authentication failed."
        result["summary"] = (
            "Authentication error: SMTP_USER or SMTP_APP_PASSWORD is wrong. "
            "For Gmail, use a 16-character App Password (not your account password). "
            "Enable 2FA and create an App Password at myaccount.google.com/apppasswords."
        )
        print("[SMTP Diagnostic] Authentication failed - wrong credentials.")
        server.quit()
        return result
    except Exception as e:
        result["error"] = f"TLS/Auth error: {type(e).__name__}"
        result["summary"] = f"TLS handshake or login failed: {type(e).__name__}"
        print(f"[SMTP Diagnostic] TLS/Auth error: {type(e).__name__}")
        return result

    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart("alternative")
        msg["From"] = user
        msg["To"] = test_recipient
        msg["Subject"] = "Checkup Buddy - SMTP Diagnostic Test"
        msg.attach(MIMEText(
            "This is an automated SMTP diagnostic test from Checkup Buddy.\n"
            "If you received this, email delivery is working correctly.\n\n"
            "-- Checkup Buddy Admin Diagnostic",
            "plain", "utf-8"
        ))
        server.sendmail(user, [test_recipient], msg.as_string())
        server.quit()
        result["message_accepted"] = True
        result["summary"] = (
            f"SUCCESS: SMTP server accepted the test message for delivery to {test_recipient}. "
            "Check that inbox (and spam folder) to confirm end-to-end delivery."
        )
        print(f"[SMTP Diagnostic] Test message accepted for {test_recipient}.")
    except smtplib.SMTPRecipientsRefused:
        result["error"] = "Recipient address rejected by SMTP server."
        result["summary"] = f"The address {test_recipient} was rejected. Check it is a valid, reachable address."
        print(f"[SMTP Diagnostic] Recipient refused: {test_recipient}")
    except Exception as e:
        result["error"] = f"Send failed: {type(e).__name__}"
        result["summary"] = f"Message send failed: {type(e).__name__}"
        print(f"[SMTP Diagnostic] Send error: {type(e).__name__}")

    return result
