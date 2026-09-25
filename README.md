# Checkup Buddy (v2) — AI-Powered Multi-Disease Health Analytics

**Checkup Buddy** is a Streamlit-based multi-disease clinical risk assessment platform engineered for preventive healthcare, automated vitals gating, and longitudinal health tracking.

---

## Key Features

1. **Role-Based Authentication**:
   - **Patient Portal**: Self-service registration secured by dual independent OTP verification (Email + SMS) with cryptographic rest-hashing (SHA-256), 5-minute expiry, max 3 attempts, and 30-second cooldown.
   - **Owner / Medical Director Portal**: Restricted access portal provisioned exclusively via CLI (`create_owner.py`) or startup environment seeding. Owner accounts cannot self-register through the public interface.
   - **PBKDF2 Password Hashing**: Passwords stored using PBKDF2-HMAC-SHA256 with 100,000 iterations and per-user cryptographic salts.
   - **Zero-UI OTP Leakage**: OTP codes are never displayed in the frontend UI. In development mode without active Twilio/SMTP credentials, OTPs are printed exclusively to the server console log.

2. **Mandatory Vitals Gating (Step 1 + Step 2)**:
   - Diagnostic modules remain strictly locked until the user completes the demographic and physiological intake (Body Temperature, Blood Pressure Systolic & Diastolic, Fasting Blood Sugar, Height & Weight for BMI).
   - Physiological sanity bounds are validated prior to unlocking assessment modules.
   - Intake parameters automatically pre-fill relevant diagnostic inputs (Age, Gender, Blood Pressure, Glucose, BMI) so users never re-enter known data.

3. **Seven Tabular Machine Learning Modules**:
   - **Heart Disease**: Cleveland Heart Disease (Random Forest, 85%+ accuracy).
   - **Diabetes**: Pima Indians Diabetes (Random Forest, 74%+ accuracy).
   - **Parkinson's Disease**: Voice acoustic harmonics & dysphonia features (SVM, 94%+ accuracy).
   - **Chronic Kidney Disease (CKD)**: Renal filtration & urinalysis indicators (Random Forest, 98%+ accuracy).
   - **Liver Disease**: Indian Liver Patient Dataset (Random Forest with balanced weighting, 70%+ accuracy).
   - **Stroke Risk**: Cerebrovascular risk factors & hemodynamics (Random Forest, balanced weighting).
   - **Breast Cancer Risk**: Fine-Needle Aspiration (FNA) nuclear morphometry (Random Forest, 93%+ accuracy, with demographic female-validation disclaimer).

4. **Hospital-Style Downloadable PDF Reports (`fpdf2`)**:
   - Professional clinic letterhead with high-resolution logo, timestamp, and unique Medical Record Number (`CB-XXXXXX`).
   - Bordered physiological vitals table with normal clinical ranges.
   - Color-coded diagnostic risk badge (Red for Elevated Risk / Green for Low Risk) and probability score.
   - Specific input features table.
   - Evidence-based lifestyle modifications, acute emergency warning signs, and physician consultation questions.

5. **Owner Administration & Audit Logging**:
   - Population health overview: Total registered patients, test distribution by disease, and risk tier stratification.
   - Searchable and sortable patient roster with test counts.
   - Read-only patient medical record inspection (vitals history and diagnostic runs).
   - Automated audit logging: Every patient file access by an Owner is immutably recorded in `owner_access_log` for regulatory compliance.
   - Strict server-side access control (`role == 'owner'`).

---

## Directory Architecture

```
checkup-buddy/
├── app.py                     # Main Streamlit application entrypoint
├── auth.py                    # Dual-OTP signup, role-based login & PBKDF2 auth
├── database.py                # Parameterized SQLite schema, CRUD & audit logging
├── otp_service.py             # OTP generation, hashing, cooldown, Twilio/SMTP/console dispatch
├── profile.py                 # Profile editing & server-side avatar compression
├── owner_dashboard.py         # Admin analytics, patient directory, & audit log
├── vitals_intake.py           # Step 1 + Step 2 mandatory clinical intake & gating
├── pdf_generator.py           # fpdf2-based hospital report builder with letterhead
├── recommendations.py         # Clinical guidance & physician discussion questions
├── create_owner.py            # Dedicated CLI tool for provisioning Owner accounts
├── modules/                   # Individual disease UI forms & inference modules
│   ├── heart.py
│   ├── diabetes.py
│   ├── parkinsons.py
│   ├── kidney.py
│   ├── liver.py
│   ├── stroke.py
│   └── breast_cancer.py
├── Datasets/                  # RAW DATA ONLY (strictly .csv files)
│   ├── heart.csv
│   ├── diabetes.csv
│   ├── parkinsons.csv
│   ├── kidney_disease.csv
│   ├── indian_liver_patient.csv
│   ├── stroke_data.csv
│   └── breast_cancer_wisconsin.csv
├── Model/                     # Interactive Jupyter training notebooks
│   ├── Heart.ipynb
│   ├── Diabetes.ipynb
│   ├── Parkinson.ipynb
│   ├── Kidney.ipynb
│   ├── Liver.ipynb
│   ├── Stroke.ipynb
│   └── BreastCancer.ipynb
├── Saved_Models/              # Serialized (.sav) model and scaler pairs
├── profile_pics/              # User-uploaded avatars (gitignored)
├── Images/                    # Logo and UI graphics
├── .env.example               # Environment variables configuration template
├── .gitignore                 # Security ignore file
├── Requirements.txt           # Python dependency specification
└── README.md                  # System documentation
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Pip

### 2. Install Dependencies
```bash
pip install -r Requirements.txt
```

### 3. Provision the Owner Account
Because owner accounts cannot self-register in the web UI for security reasons, provision an owner via the dedicated CLI script:
```bash
python create_owner.py --username admin --email admin@hospital.com --password YourSecurePassword123
```
Alternatively, configure `OWNER_EMAIL` and `OWNER_PASSWORD` in your `.env` file for automatic initialization upon first run.

### 4. (Optional) Re-train Models & Generate Notebooks
All 7 models and Jupyter notebooks are pre-generated. To retrain from the raw datasets at any time:
```bash
python train_all_models.py
```

### 5. Launch the Application
```bash
streamlit run app.py
```

---

## 🚀 Streamlit Community Cloud Deployment Guide

Checkup Buddy is pre-configured for one-click deployment on **Streamlit Community Cloud**:

### Step 1: Push to GitHub
1. Initialize git and commit your project (ensure `.env` and `.streamlit/secrets.toml` remain gitignored):
   ```bash
   git init
   git add .
   git commit -m "feat: Checkup Buddy production release"
   git branch -M main
   git remote add origin https://github.com/your-username/your-repo-name.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud
1. Navigate to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
2. Click **"New app"**.
3. Select your repository, branch (`main`), and set the main file path to `app.py`.
4. Click **"Advanced settings..."** or **"App Settings" -> "Secrets"**.

### Step 3: Configure Secrets in Streamlit Cloud
Copy and paste the following block directly into the **Secrets** text box (or copy from your local `.streamlit/secrets.toml`):

```toml
# --- Gmail SMTP Configuration (for live Email OTP delivery) ---
SMTP_USER = "your_email@gmail.com"
SMTP_APP_PASSWORD = "your_16_char_app_password"

# --- Owner / Administrator Account ---
OWNER_EMAIL = "admin@example.com"
OWNER_PASSWORD = "your_secure_password"
OWNER_USERNAME = "admin"

# --- Optional: Twilio SMS (if mobile OTP is enabled) ---
# TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# TWILIO_AUTH_TOKEN = "your_auth_token"
# TWILIO_PHONE_NUMBER = "+1234567890"
```

5. Click **"Save"** and **"Deploy!"**.
   - The app will automatically read secrets via `st.secrets`.
   - The Owner account will automatically be seeded upon initial startup.
   - If secrets are missing, the app gracefully falls back to secure dev-mode logging without crashing.

---

## Security & Compliance Notice
- All database queries use SQLite parameterization (`?`) to prevent SQL injection vulnerabilities.
- Verification codes (OTPs) are hashed at rest using SHA-256 and never transmitted to the browser UI.
- Medical disclaimers are prominently displayed across every diagnostic screen and PDF document.
- Patients are strictly scoped to their own data (`WHERE user_id = session_state.user_id`).
- Secrets and credentials are never checked into version control.
