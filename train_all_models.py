"""
Model training and notebook generation script for Checkup Buddy (v2).
Trains RandomForest and SVM models for all 7 disease modules,
exports (.sav) model and scaler pairs to Saved_Models/,
and generates clean interactive Jupyter notebooks in Model/.
"""

import os
import json
import pickle
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(BASE_DIR, "Datasets")
SAVED_MODELS_DIR = os.path.join(BASE_DIR, "Saved_Models")
MODEL_NOTEBOOKS_DIR = os.path.join(BASE_DIR, "Model")

os.makedirs(SAVED_MODELS_DIR, exist_ok=True)
os.makedirs(MODEL_NOTEBOOKS_DIR, exist_ok=True)


def create_jupyter_notebook(notebook_path, title, description, code_cells):
    """Generates a standard .ipynb JSON file."""
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {title}\n", f"\n{description}\n"]
        }
    ]
    for code in code_cells:
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in code.strip().split("\n")]
        })

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }

    with open(notebook_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=2)
    print(f"Generated notebook: {notebook_path}")


# ---------------- 1. HEART DISEASE ----------------
def train_heart():
    print("--- Training Heart Disease Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "heart.csv"))
    X = df.drop(columns=["target"])
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Heart Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "heart_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "heart_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Heart.ipynb"),
        "Heart Disease Risk Prediction Model",
        "Trained using UCI Cleveland Heart Disease dataset with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/heart.csv')\ndf.head()",
            "X = df.drop(columns=['target'])\ny = df['target']\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)",
            "scaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/heart_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/heart_scaler.sav', 'wb'))\nprint('Saved Heart model and scaler successfully!')"
        ]
    )


# ---------------- 2. DIABETES ----------------
def train_diabetes():
    print("--- Training Diabetes Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "diabetes.csv"))
    X = df.drop(columns=["Outcome"])
    y = df["Outcome"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Diabetes Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "diabetes_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "diabetes_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Diabetes.ipynb"),
        "Diabetes Risk Prediction Model",
        "Trained using Pima Indians Diabetes dataset with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/diabetes.csv')\ndf.head()",
            "X = df.drop(columns=['Outcome'])\ny = df['Outcome']\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)",
            "scaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/diabetes_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/diabetes_scaler.sav', 'wb'))\nprint('Saved Diabetes model and scaler successfully!')"
        ]
    )


# ---------------- 3. PARKINSON'S ----------------
def train_parkinsons():
    print("--- Training Parkinson's Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "parkinsons.csv"))
    X = df.drop(columns=["name", "status"])
    y = df["status"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = SVC(kernel="linear", probability=True, random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Parkinson's Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "parkinsons_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "parkinsons_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Parkinson.ipynb"),
        "Parkinson's Disease Risk Prediction Model",
        "Trained using UCI Parkinson's voice acoustics dataset with Support Vector Machine (SVM).",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.svm import SVC\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/parkinsons.csv')\ndf.head()",
            "X = df.drop(columns=['name', 'status'])\ny = df['status']\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)",
            "scaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = SVC(kernel='linear', probability=True, random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/parkinsons_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/parkinsons_scaler.sav', 'wb'))\nprint('Saved Parkinson model and scaler successfully!')"
        ]
    )


# ---------------- 4. CHRONIC KIDNEY DISEASE ----------------
def train_kidney():
    print("--- Training Chronic Kidney Disease Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "kidney_disease.csv"))

    # Clean target: 'ckd', 'ckd\t' -> 1, 'notckd' -> 0
    df["class"] = df["class"].astype(str).str.strip().replace({"ckd": 1, "notckd": 0})
    df = df[df["class"].isin([0, 1])].copy()
    df["class"] = df["class"].astype(int)

    # Key clinical features for assessment:
    # age, bp, sg, al, su, bgr (blood glucose random), bu (blood urea), sc (serum creatinine), hemo, pcv
    features = ["age", "bp", "sg", "al", "su", "bgr", "bu", "sc", "hemo", "pcv"]
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

    X = df[features]
    y = df["class"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Kidney Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "kidney_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "kidney_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Kidney.ipynb"),
        "Chronic Kidney Disease Prediction Model",
        "Trained using UCI Chronic Kidney Disease dataset with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/kidney_disease.csv')\ndf['class'] = df['class'].astype(str).str.strip().replace({'ckd': 1, 'notckd': 0})\ndf = df[df['class'].isin([0, 1])].copy()\ndf['class'] = df['class'].astype(int)",
            "features = ['age', 'bp', 'sg', 'al', 'su', 'bgr', 'bu', 'sc', 'hemo', 'pcv']\nfor col in features:\n    df[col] = pd.to_numeric(df[col], errors='coerce')\n    df[col] = df[col].fillna(df[col].median())\nX = df[features]\ny = df['class']",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\nscaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/kidney_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/kidney_scaler.sav', 'wb'))\nprint('Saved Kidney model and scaler successfully!')"
        ]
    )


# ---------------- 5. LIVER DISEASE ----------------
def train_liver():
    print("--- Training Liver Disease Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "indian_liver_patient.csv"))

    # Map Gender: Male: 1, Female: 0
    df["Gender"] = df["Gender"].astype(str).str.strip().map({"Male": 1, "Female": 0}).fillna(1).astype(int)
    # Target 'Selector': 1 = liver patient (disease present -> 1), 2 = not liver patient (0)
    df["Selector"] = df["Selector"].map({1: 1, 2: 0})

    # Impute missing values (A/G Ratio)
    for col in df.columns:
        if col != "Selector":
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(df[col].median())

    features = ["Age", "Gender", "TB", "DB", "Alkphos", "Sgpt", "Sgot", "TP", "ALB", "A/G Ratio"]
    X = df[features]
    y = df["Selector"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight="balanced", random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Liver Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "liver_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "liver_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Liver.ipynb"),
        "Indian Liver Patient Disease Prediction Model",
        "Trained using Indian Liver Patient Dataset (ILPD) with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/indian_liver_patient.csv')\ndf['Gender'] = df['Gender'].astype(str).str.strip().map({'Male': 1, 'Female': 0}).fillna(1).astype(int)\ndf['Selector'] = df['Selector'].map({1: 1, 2: 0})\nfeatures = ['Age', 'Gender', 'TB', 'DB', 'Alkphos', 'Sgpt', 'Sgot', 'TP', 'ALB', 'A/G Ratio']\nfor col in features:\n    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median())\nX = df[features]\ny = df['Selector']",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\nscaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced', random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/liver_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/liver_scaler.sav', 'wb'))\nprint('Saved Liver model and scaler successfully!')"
        ]
    )


# ---------------- 6. STROKE RISK ----------------
def train_stroke():
    print("--- Training Stroke Risk Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "stroke_data.csv"))

    # Features: age, hypertension, heart_disease, avg_glucose_level, bmi, gender, ever_married, smoking_status
    df["gender"] = df["gender"].map({"Male": 1, "Female": 0}).fillna(0).astype(int)
    df["ever_married"] = df["ever_married"].map({"Yes": 1, "No": 0}).fillna(0).astype(int)
    # Smoking: 0: never, 1: formerly, 2: smokes, 3: unknown
    smoking_map = {"never smoked": 0, "formerly smoked": 1, "smokes": 2, "Unknown": 3}
    df["smoking_status"] = df["smoking_status"].map(smoking_map).fillna(3).astype(int)

    df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    features = ["gender", "age", "hypertension", "heart_disease", "ever_married", "avg_glucose_level", "bmi", "smoking_status"]
    X = df[features]
    y = df["stroke"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight="balanced", random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Stroke Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "stroke_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "stroke_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "Stroke.ipynb"),
        "Stroke Risk Prediction Model",
        "Trained using Kaggle Stroke Prediction Dataset with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/stroke_data.csv')\ndf['gender'] = df['gender'].map({'Male': 1, 'Female': 0}).fillna(0).astype(int)\ndf['ever_married'] = df['ever_married'].map({'Yes': 1, 'No': 0}).fillna(0).astype(int)\nsmoking_map = {'never smoked': 0, 'formerly smoked': 1, 'smokes': 2, 'Unknown': 3}\ndf['smoking_status'] = df['smoking_status'].map(smoking_map).fillna(3).astype(int)\ndf['bmi'] = pd.to_numeric(df['bmi'], errors='coerce').fillna(df['bmi'].median())",
            "features = ['gender', 'age', 'hypertension', 'heart_disease', 'ever_married', 'avg_glucose_level', 'bmi', 'smoking_status']\nX = df[features]\ny = df['stroke']",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\nscaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=5, class_weight='balanced', random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/stroke_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/stroke_scaler.sav', 'wb'))\nprint('Saved Stroke model and scaler successfully!')"
        ]
    )


# ---------------- 7. BREAST CANCER ----------------
def train_breast_cancer():
    print("--- Training Breast Cancer Model ---")
    df = pd.read_csv(os.path.join(DATASETS_DIR, "breast_cancer_wisconsin.csv"))

    # In sklearn WDBC, target: 0 = malignant (Risk Detected -> 1), 1 = benign (No Significant Risk -> 0)
    # We map 0 -> 1 (Risk Detected), 1 -> 0 (Normal) for clinical consistency
    y = df["target"].map({0: 1, 1: 0})

    # The 10 core nuclear morphology features from FNA biopsy:
    features = [
        "mean radius", "mean texture", "mean perimeter", "mean area",
        "mean smoothness", "mean compactness", "mean concavity",
        "mean concave points", "mean symmetry", "mean fractal dimension"
    ]
    X = df[features]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train_scaled, y_train)

    acc = accuracy_score(y_test, model.predict(X_test_scaled))
    print(f"Breast Cancer Test Accuracy: {acc * 100:.2f}%")

    with open(os.path.join(SAVED_MODELS_DIR, "breast_cancer_model.sav"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(SAVED_MODELS_DIR, "breast_cancer_scaler.sav"), "wb") as f:
        pickle.dump(scaler, f)

    create_jupyter_notebook(
        os.path.join(MODEL_NOTEBOOKS_DIR, "BreastCancer.ipynb"),
        "Wisconsin Breast Cancer Risk Prediction Model",
        "Trained using Wisconsin Diagnostic Breast Cancer (WDBC) nuclear FNA parameters with Random Forest Classifier.",
        [
            "import pandas as pd\nimport numpy as np\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nfrom sklearn.ensemble import RandomForestClassifier\nfrom sklearn.metrics import accuracy_score, classification_report\nimport pickle",
            "df = pd.read_csv('../Datasets/breast_cancer_wisconsin.csv')\n# Target mapping: 0 (Malignant) -> 1 (Risk Detected), 1 (Benign) -> 0 (No Risk)\ny = df['target'].map({0: 1, 1: 0})",
            "features = ['mean radius', 'mean texture', 'mean perimeter', 'mean area', 'mean smoothness', 'mean compactness', 'mean concavity', 'mean concave points', 'mean symmetry', 'mean fractal dimension']\nX = df[features]",
            "X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)\nscaler = StandardScaler()\nX_train_scaled = scaler.fit_transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
            "model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)\nmodel.fit(X_train_scaled, y_train)\ny_pred = model.predict(X_test_scaled)\nprint('Accuracy:', accuracy_score(y_test, y_pred))\nprint(classification_report(y_test, y_pred))",
            "pickle.dump(model, open('../Saved_Models/breast_cancer_model.sav', 'wb'))\npickle.dump(scaler, open('../Saved_Models/breast_cancer_scaler.sav', 'wb'))\nprint('Saved Breast Cancer model and scaler successfully!')"
        ]
    )


if __name__ == "__main__":
    train_heart()
    train_diabetes()
    train_parkinsons()
    train_kidney()
    train_liver()
    train_stroke()
    train_breast_cancer()
    print("\n[ALL 7 MODELS TRAINED AND NOTEBOOKS GENERATED SUCCESSFULLY]")
