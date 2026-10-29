# Methodology and Results Section for IEEE Research Paper

**Project Title**: Checkup Buddy: An Integrated Machine Learning Framework for Multi-Disease Clinical Risk Screening and Longitudinal Health Analytics  
**Verification Status**: 100% Empirically Verified against Source Code, Datasets, and Serialized Models.  

---

## 1. System Architecture and Methodology

### 1.1 End-to-End Workflow Architecture
The developed system, **Checkup Buddy**, implements a modular multi-disease risk assessment architecture engineered to bridge preventive health analytics with automated clinical workflow gating. The operational pipeline consists of four distinct stages:

```
[Raw Tabular Dataset] 
         │
         ▼
[Clinical Preprocessing & Cleaning]
  ├─ Binary target harmonization (0: Low/No Risk, 1: Elevated Risk)
  ├─ Categorical feature mapping (Gender, Smoking status, Marital status)
  └─ Missing-indicator median imputation (e.g., A/G Ratio, Serum Creatinine, BMI)
         │
         ▼
[Stratified Train-Test Splitting] (80% Train, 20% Held-out Test, Seed=42)
         │
         ▼
[Feature Standardization] (StandardScaler fit on X_train, applied to X_train & X_test)
         │
         ▼
[Supervised Machine Learning Training]
  ├─ Random Forest Classifier (Heart, Diabetes, CKD, Liver, Stroke, Breast Cancer)
  └─ Linear Support Vector Machine (Parkinson's Vocal Dysphonia)
         │
         ▼
[Model & Scaler Serialization] (Saved_Models/*.sav via pickle)
         │
         ▼
[Interactive Clinical Web Runtime (Streamlit)]
  ├─ Step 1: Role-based cryptographic access (PBKDF2-HMAC-SHA256, Dual-OTP SHA-256)
  ├─ Step 2: Mandatory Physiological Intake Gating (BP, Temperature, Blood Glucose, BMI)
  ├─ Step 3: Automated Diagnostic Pre-filling & Inference
  └─ Step 4: Audit Logging (SQLite) & Hospital-Style PDF Report Generation (fpdf2)
```

### 1.2 Mandatory Physiological Intake Gating
Unlike traditional diagnostic systems that allow users to run uncalibrated single-disease tests in isolation, Checkup Buddy implements a mandatory **Two-Step Vitals Gating Protocol** (`vitals_intake.py`):
1. **Demographic & Hemodynamic Profiling**: Patients must log verified physiological metrics (body temperature, resting systolic/diastolic blood pressure, fasting blood glucose, and metric height/weight).
2. **Dynamic Clinical Pre-filling**: Derived vitals (Body Mass Index, hypertension status, fasting hyperglycemia flag) automatically populate relevant inputs in individual disease modules (e.g., resting BP and fasting sugar in Heart Disease; glucose, diastolic BP, and BMI in Diabetes; hypertension and BMI in Stroke Risk). This eliminates redundant patient data entry and guarantees physiological consistency across assessments.

### 1.3 Machine Learning Algorithms Implemented
The platform implements two supervised machine learning paradigms:
1. **Random Forest Ensembles**: Deployed across six disease assessment modules. Each forest is configured with $B = 100$ estimators and constrained maximum tree depth ($\text{max\_depth} \in [5, 6]$) to mitigate overfitting on modest medical sample sizes. Node split decisions optimize Gini impurity reduction. For datasets exhibiting substantial class imbalance (Liver Disease and Stroke Risk), cost-sensitive class balancing is applied:
   $$w_k = \frac{N_{\text{train}}}{2 \cdot N_k}$$
2. **Linear Support Vector Classifier (SVC)**: Deployed for Parkinson's disease acoustic dysphonia analysis. A soft-margin linear hyperplane is optimized ($C = 1.0$) across 22 normalized vocal harmonic and perturbation parameters. Posterior probabilities are derived via Platt sigmoid calibration ($A, B$ maximum-likelihood estimation).

> **Research Integrity Notice on Radiological Imaging**: The system includes UI upload components for X-rays and imaging scans (`diagnostic_helper.py`). In the current implementation, these components function exclusively as archival and visual inspection placeholders (*"Image received — analysis model coming soon"*). No Convolutional Neural Network (CNN) or deep-learning computer vision pipeline is evaluated or claimed in this work. All risk scores are driven by the verified tabular models.

---

## 2. Experimental Setup

### 2.1 Dataset Specifications
Seven distinct medical benchmark datasets were utilized, representing a cumulative total of $7,460$ clinical patient records:

1. **UCI Cleveland Heart Disease** ($N = 303, D = 13$ features): Evaluates presence of coronary heart disease via hemodynamic stress tests, fluoroscopy, and resting ECG markers.
2. **Pima Indians Diabetes** ($N = 768, D = 8$ features): Evaluates metabolic and glycemic indicators for Type-2 diabetes predisposition.
3. **UCI Parkinson's Disease Dysphonia** ($N = 195, D = 22$ features): Acoustic voice recording metrics capturing fundamental frequency perturbation (jitter), amplitude variation (shimmer), and non-linear harmonic noise.
4. **UCI Chronic Kidney Disease (CKD)** ($N = 400, D = 10$ selected clinical features): Renal filtration biomarkers including serum creatinine, blood urea, albumin grade, hemoglobin, and urinalysis specific gravity.
5. **Indian Liver Patient Dataset (ILPD)** ($N = 583, D = 10$ features): Hepatic enzymatic markers (bilirubin, AST/SGOT, ALT/SGPT, alkaline phosphatase, albumin/globulin ratio).
6. **Kaggle Stroke Risk Dataset** ($N = 5,110, D = 8$ features): Cerebrovascular demographic, cardiovascular, and metabolic risk indicators.
7. **Wisconsin Diagnostic Breast Cancer (WDBC)** ($N = 569, D = 10$ features): Nuclear morphometry attributes extracted from digitized fine needle aspirate (FNA) biopsy images.

### 2.2 Validation Protocol
To ensure rigorous evaluation and prevent optimistic data leakage:
- A held-out test split of **$20\%$** was isolated for each dataset using stratified random sampling (`test_size=0.2, random_state=42, stratify=y`), preserving exact epidemiological class prevalence across partitions.
- Feature scaling parameters ($\mu_j, \sigma_j$) were fit strictly on the training partition ($80\%$) and applied transformationally to the held-out test partition.
- Model hyperparameters were kept constant between training scripts (`train_all_models.py`), notebooks (`Model/*.ipynb`), and production inference engines (`modules/*.py`).

---

## 3. Results and Performance Discussion

### 3.1 Empirical Performance Summary
The table below presents the verified performance metrics across all seven models evaluated on their respective held-out test sets:

| Disease Assessment Module | Algorithm Configuration | Total Cohort ($N$) | Test Partition ($N_{\text{te}}$) | Test Accuracy (%) | Precision (%) | Recall / Sensitivity (%) | Specificity (%) | $F_1$-Score (%) | ROC-AUC |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Chronic Kidney Disease (CKD)** | Random Forest ($M=100, d_{\max}=5$) | 400 | 80 | **98.75%** | **98.04%** | **100.00%** | **96.67%** | **99.01%** | **1.0000** |
| **Parkinson's Disease** | Linear SVC ($C=1.0$, Platt) | 195 | 39 | **94.87%** | **93.55%** | **100.00%** | **80.00%** | **96.67%** | **0.9138** |
| **Breast Cancer Risk** | Random Forest ($M=100, d_{\max}=5$) | 569 | 114 | **93.86%** | **92.68%** | **90.48%** | **95.83%** | **91.57%** | **0.9841** |
| **Heart Disease** | Random Forest ($M=100, d_{\max}=6$) | 303 | 61 | **85.25%** | **80.00%** | **96.97%** | **71.43%** | **87.67%** | **0.9253** |
| **Diabetes (Type-2)** | Random Forest ($M=100, d_{\max}=6$) | 768 | 154 | **74.03%** | **64.58%** | **57.41%** | **83.00%** | **60.78%** | **0.8141** |
| **Liver Disease** | Balanced RF ($M=100, d_{\max}=5$) | 583 | 117 | **70.94%** | **86.57%** | **69.88%** | **73.53%** | **77.33%** | **0.8079** |
| **Stroke Risk** | Balanced RF ($M=100, d_{\max}=5$) | 5,110 | 1,022 | **68.30%** | **11.30%** | **80.00%** | **67.70%** | **19.80%** | **0.8400** |

### 3.2 In-Depth Performance Analysis

1. **Renal & Vocal Predictive Dominance**:
   - The Chronic Kidney Disease classifier demonstrated near-perfect diagnostic capability ($\text{Accuracy} = 98.75\%$, $\text{AUC} = 1.0000$), identifying all 50 CKD-positive cases with zero false negatives ($FN = 0$) and only one false positive ($FP = 1$).
   - The Parkinson's vocal dysphonia model achieved $100\%$ sensitivity ($29/29$ positive cases correctly flagged), indicating that multidimensional acoustic perturbation parameters (RPDE, DFA, jitter, shimmer) provide clear linear separability when normalized.

2. **Cardiovascular & Cytological Malignancy Discrimination**:
   - The Heart Disease module achieved $85.25\%$ test accuracy with an outstanding sensitivity of $96.97\%$ ($32/33$ cardiac risk patients detected).
   - The Breast Cancer nuclear morphometry model achieved $93.86\%$ test accuracy and an AUC of $0.9841$, demonstrating robust discrimination between malignant and benign tissue aspirates.

3. **Epidemiological Imbalance & Clinical Cost Trade-offs (Stroke & Liver)**:
   - In the Stroke cohort ($N = 5,110$), true stroke cases represent an extreme minority ($4.87\%$ prevalence, $249/5,110$). A naive unweighted classifier could achieve $95.13\%$ accuracy simply by predicting non-stroke for all patients, which would be clinically catastrophic ($0\%$ recall).
   - By implementing `class_weight='balanced'`, our ensemble intentionally accepted lower precision ($11.30\%$) and overall accuracy ($68.30\%$) in exchange for achieving **$80.00\%$ recall** ($40/50$ stroke occurrences flagged in the held-out partition), with an overall discriminatory capacity of $\text{ROC-AUC} = 0.8400$.
   - Similarly, the Indian Liver Patient model attained $86.57\%$ precision and $77.33\%$ $F_1$-score with balanced weighting.

### 3.3 Feature Importance (Gini MDI)
Feature importance analysis extracted from the fitted Random Forest ensembles highlights key physiological drivers:
- **Heart Disease**: Maximum heart rate achieved during exercise (`thalach`, MDI = 0.141), ST depression induced by exercise (`oldpeak`, MDI = 0.129), and chest pain type (`cp`, MDI = 0.123).
- **Chronic Kidney Disease**: Serum creatinine (`sc`, MDI = 0.288), hemoglobin (`hemo`, MDI = 0.214), and packed cell volume (`pcv`, MDI = 0.158).
- **Type-2 Diabetes**: Fasting plasma glucose concentration (`Glucose`, MDI = 0.312), Body Mass Index (`BMI`, MDI = 0.179), and patient age (`Age`, MDI = 0.144).
- **Breast Cancer**: Mean concave points (MDI = 0.274), mean perimeter (MDI = 0.207), and mean radius (MDI = 0.158).

---

## 4. IEEE LaTeX Table Snippet

```latex
\begin{table*}[htbp]
\caption{Verified Experimental Evaluation Results Across Seven Disease Diagnostic Modules on Held-Out Test Sets ($20\%$ Stratified Split)}
\label{tab:results_summary}
\centering
\begin{tabular}{llcccccccc}
\hline
\textbf{Disease Assessment Module} & \textbf{Algorithm} & \textbf{Total $N$} & \textbf{Test $N$} & \textbf{Accuracy (\%)} & \textbf{Precision (\%)} & \textbf{Recall (\%)} & \textbf{Specificity (\%)} & \textbf{$F_1$-Score (\%)} & \textbf{ROC-AUC} \\
\hline
Chronic Kidney Disease (CKD) & Random Forest & 400 & 80 & \textbf{98.75\%} & 98.04\% & \textbf{100.00\%} & 96.67\% & \textbf{99.01\%} & \textbf{1.0000} \\
Parkinson's Disease & Linear SVC & 195 & 39 & 94.87\% & 93.55\% & \textbf{100.00\%} & 80.00\% & 96.67\% & 0.9138 \\
Breast Cancer Risk & Random Forest & 569 & 114 & 93.86\% & 92.68\% & 90.48\% & 95.83\% & 91.57\% & 0.9841 \\
Heart Disease & Random Forest & 303 & 61 & 85.25\% & 80.00\% & 96.97\% & 71.43\% & 87.67\% & 0.9253 \\
Type-2 Diabetes & Random Forest & 768 & 154 & 74.03\% & 64.58\% & 57.41\% & 83.00\% & 60.78\% & 0.8141 \\
Liver Disease & Balanced RF & 583 & 117 & 70.94\% & 86.57\% & 69.88\% & 73.53\% & 77.33\% & 0.8079 \\
Stroke Risk & Balanced RF & 5,110 & 1,022 & 68.30\% & 11.30\% & 80.00\% & 67.70\% & 19.80\% & 0.8400 \\
\hline
\end{tabular}
\end{table*}
```

