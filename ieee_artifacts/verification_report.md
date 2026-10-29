# Verification and Traceability Report

**Project**: Checkup Buddy (v2) — Multi-Disease Health Analytics  
**Date of Audit**: October 28, 2026  
**Auditor**: ML Research Assistant & Verification Engine  
**Status**: Fully Verified and Reproducible (Zero Fabricated Metrics)  

---

## 1. Traceability Matrix

### 1.1 Mathematical Formulas Traceability
| Equation ID / Concept | LaTeX Equation Label | Source Code File | Function / Code Reference | Verification Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Body Mass Index (BMI)** | `\label{eq:bmi}` | `vitals_intake.py` | `calculate_bmi()` (Lines 12–30) | Exact Quetelet metric implementation: $\text{weight} / (\text{height}/100)^2$. |
| **Hypertension Indicator** | `\label{eq:htn}` | `modules/stroke.py` | Line 82 (`vitals_bp_sys >= 130 or vitals_bp_dia >= 85`) | Auto-populated binary threshold from active intake session. |
| **Fasting Blood Sugar Flag** | `\label{eq:fbs}` | `modules/heart.py` | Line 52 (`vitals.get('blood_sugar') > 120`) | Clinical threshold used in Cleveland Heart Disease dataset. |
| **Z-Score Normalization** | `\label{eq:standard_scaler}` | `train_all_models.py` | `StandardScaler().fit_transform(X_train)` (Lines 76–78, 114–116, etc.) | Fit strictly on training set; applied to test set via `transform()`. |
| **Gini Impurity & Tree Split** | `\label{eq:gini}`, `\label{eq:split_gain}` | `train_all_models.py` | `RandomForestClassifier(criterion='gini', ...)` | Default scikit-learn splitting criterion across all 6 RF models. |
| **Balanced Class Weighting** | `\label{eq:class_weight}` | `train_all_models.py` | `class_weight='balanced'` in `train_liver()` (Line 258) & `train_stroke()` (Line 307) | Inversely weights classes based on sample prevalence. |
| **Ensemble Soft Voting** | `\label{eq:ensemble_prob}` | `modules/*.py` | `model.predict_proba(scaled)[0][1]` | Probability averaged over $B=100$ trees. |
| **Linear SVM Primal & Margin** | `\label{eq:svm_primal}` | `train_all_models.py` | `SVC(kernel='linear', C=1.0)` in `train_parkinsons()` (Line 156) | Soft-margin linear support vector optimization. |
| **Platt Probability Scaling** | `\label{eq:platt_scaling}` | `train_all_models.py` | `SVC(..., probability=True)` (Line 156) | Internal 5-fold CV maximum-likelihood sigmoid calibration. |

---

### 1.2 Experimental Metrics Traceability
Every metric reported in `results_summary.csv` and `methodology_and_results.md` was reproduced directly using the serialized models and test splits:

| Disease Module | Trained Model Artifact | Trained Scaler Artifact | Held-Out Test Data Split | Verified Test Accuracy | Verified Precision | Verified Recall | Verified F1-Score | Verified ROC-AUC |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Heart Disease** | `Saved_Models/heart_model.sav` | `Saved_Models/heart_scaler.sav` | `Datasets/heart.csv` ($20\%$, $N=61$) | **85.25%** | **80.00%** | **96.97%** | **87.67%** | **0.9253** |
| **Type-2 Diabetes** | `Saved_Models/diabetes_model.sav` | `Saved_Models/diabetes_scaler.sav` | `Datasets/diabetes.csv` ($20\%$, $N=154$) | **74.03%** | **64.58%** | **57.41%** | **60.78%** | **0.8141** |
| **Parkinson's Disease** | `Saved_Models/parkinsons_model.sav` | `Saved_Models/parkinsons_scaler.sav` | `Datasets/parkinsons.csv` ($20\%$, $N=39$) | **94.87%** | **93.55%** | **100.00%** | **96.67%** | **0.9138** |
| **Chronic Kidney Disease** | `Saved_Models/kidney_model.sav` | `Saved_Models/kidney_scaler.sav` | `Datasets/kidney_disease.csv` ($20\%$, $N=80$) | **98.75%** | **98.04%** | **100.00%** | **99.01%** | **1.0000** |
| **Liver Disease** | `Saved_Models/liver_model.sav` | `Saved_Models/liver_scaler.sav` | `Datasets/indian_liver_patient.csv` ($20\%$, $N=117$) | **70.94%** | **86.57%** | **69.88%** | **77.33%** | **0.8079** |
| **Stroke Risk** | `Saved_Models/stroke_model.sav` | `Saved_Models/stroke_scaler.sav` | `Datasets/stroke_data.csv` ($20\%$, $N=1022$) | **68.30%** | **11.30%** | **80.00%** | **19.80%** | **0.8400** |
| **Breast Cancer Risk** | `Saved_Models/breast_cancer_model.sav` | `Saved_Models/breast_cancer_scaler.sav` | `Datasets/breast_cancer_wisconsin.csv` ($20\%$, $N=114$) | **93.86%** | **92.68%** | **90.48%** | **91.57%** | **0.9841** |

---

### 1.3 Generated Figures & Data Backing Traceability
| Figure Filename | Format | Underlying CSV Data File | Source Generation Script | Clinical Interpretation & Verification |
| :--- | :--- | :--- | :--- | :--- |
| `fig1_model_performance_comparison` | PNG (300 DPI) & Vector PDF | `csv_data/fig1_model_performance_comparison.csv` | `generate_ieee_artifacts.py` (Lines 280–330) | Grouped 4-metric comparison across all 7 test partitions. All values match confusion matrices. |
| `fig2_roc_curves_all_models` | PNG (300 DPI) & Vector PDF | `csv_data/fig2_roc_curves_data.csv` | `generate_ieee_artifacts.py` (Lines 333–370) | Plotted from true labels and raw predicted probability distributions. No interpolated or synthetic points. |
| `fig3_confusion_matrices_grid` | PNG (300 DPI) & Vector PDF | `csv_data/fig3_confusion_matrices.csv` | `generate_ieee_artifacts.py` (Lines 373–420) | $2 \times 4$ heatmap grid showing exact counts ($TN, FP, FN, TP$) and cell percentages. |
| `fig4_feature_importance_analysis` | PNG (300 DPI) & Vector PDF | `csv_data/fig4_feature_importances.csv` | `generate_ieee_artifacts.py` (Lines 423–470) | Top 10 predictors for Heart, CKD, Diabetes, and Breast Cancer using fitted RF `feature_importances_`. SVC excluded. |
| `fig5_class_distribution_and_imbalance` | PNG (300 DPI) & Vector PDF | `csv_data/fig5_dataset_and_test_distributions.csv` | `generate_ieee_artifacts.py` (Lines 473–530) | Total dataset scale (log-scale) and class prevalence percentages highlighting severe skewness in Stroke ($4.87\%$). |

---

## 2. Methodological & Data Hygiene Verification

1. **Absence of Data Leakage**:
   - `StandardScaler` is fit exclusively on `X_train` (`scaler.fit_transform(X_train)`), and applied to `X_test` via `scaler.transform(X_test)`. The saved scaler objects in `Saved_Models/*_scaler.sav` store solely the training partition statistics ($\mu_j, \sigma_j$).
   - Train/test splitting enforces stratification (`stratify=y`) with `random_state=42`, ensuring test distributions accurately mirror population class ratios.
2. **Missing Value Imputation**:
   - Imputations (`median()`) are calculated per column on numeric fields (`kidney_disease.csv`, `stroke_data.csv`, `indian_liver_patient.csv`) prior to scaling.
3. **Absence of Deep Learning / CNN Models**:
   - `diagnostic_helper.py` provides an image upload widget for patient X-rays or ECG scans. The code contains an explicit disclaimer: *"AI-assisted radiological imaging analysis is currently in development."* No CNN architecture (ResNet, VGG, DenseNet) exists in the codebase. Claiming vision results in the paper would constitute academic misconduct; the paper methodology accurately describes the system as tabular-driven.
4. **Non-Iterative Training Mechanics**:
   - Because Random Forest and Support Vector Machines solve tree partitioning and convex quadratic programs without epoch-wise backpropagation, epoch loss curves do not exist. This is honestly documented.

---

## 3. Environment Specifications

- **Python Version**: 3.14.6 (64-bit)
- **Scikit-Learn Version**: 1.9.0
- **Pandas Version**: 3.0.3
- **NumPy Version**: 2.4.6
- **Matplotlib Version**: 3.11.2
- **Seaborn Version**: 0.13.2
- **FPDF2 Version**: 2.8.7
- **Operating System**: Microsoft Windows 11
- **Working Directory**: `d:\New_Major_Project`
- **Artifacts Output Path**: `d:\New_Major_Project\ieee_artifacts\`

