# SAMS — Payment Risk Prediction Model
### Student Accommodation Management System · ML Project Guide

---

## 📁 Project Structure

```
sams_ml/
├── colab/
│   └── SAMS_Payment_Risk_Prediction.py   ← Run this in Google Colab
├── web/
│   ├── app.py                            ← Flask REST API
│   ├── models/                           ← Drop .pkl files here after training
│   │   ├── sams_xgb_model.pkl
│   │   ├── sams_rf_model.pkl
│   │   ├── sams_lr_model.pkl
│   │   ├── sams_scaler.pkl
│   │   ├── sams_le_accommodation.pkl
│   │   ├── sams_le_trend.pkl
│   │   └── training_logs.json
│   └── static/
│       └── index.html                    ← Frontend UI
├── requirements.txt
└── README.md
```

# Payment Risk Machine Learning Model
## Overview
<img width="942" height="432" alt="Capture" src="https://github.com/user-attachments/assets/971ae471-a809-42d9-a78d-53b2fb4911a5" />
<img width="944" height="431" alt="Capture4" src="https://github.com/user-attachments/assets/553d9b3d-0b37-4c3f-8d3f-177ba0aafa8a" />
<img width="944" height="428" alt="Capture3" src="https://github.com/user-attachments/assets/f71f70fa-2e51-486f-9ca6-c2b938a9fd07" />
<img width="940" height="427" alt="Capture2" src="https://github.com/user-attachments/assets/a79bef87-0786-4da2-82d6-77025ccef1e3" />



---

## 🚀 Step-by-Step Guide

### STEP 1 — Run the Google Colab Notebook

1. Open [Google Colab](https://colab.research.google.com)
2. Upload `colab/SAMS_Payment_Risk_Prediction.py`
3. Or paste sections one-by-one into cells
4. Run all sections top-to-bottom
5. Download the generated `.pkl` files from the Colab file browser

**What Colab generates:**
| File | Description |
|------|-------------|
| `sams_dataset.csv` | 1,000-row synthetic dataset |
| `sams_xgb_model.pkl` | Best model (XGBoost, tuned) |
| `sams_rf_model.pkl` | Random Forest model |
| `sams_lr_model.pkl` | Logistic Regression model |
| `sams_scaler.pkl` | StandardScaler |
| `sams_le_accommodation.pkl` | Label encoder |
| `sams_le_trend.pkl` | Label encoder |
| `training_logs.json` | All metrics & CV results |
| `eda_distributions.png` | EDA plots |
| `eda_correlation.png` | Correlation heatmap |
| `confusion_matrices.png` | Confusion matrices |
| `roc_curves.png` | ROC curves |
| `model_comparison.png` | Performance comparison |
| `feature_importance.png` | Feature importances |

---

### STEP 2 — Set Up the Flask API

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy your .pkl files into web/models/
mkdir web/models
cp sams_*.pkl web/models/
cp training_logs.json web/models/

# Start the API server
cd web
python app.py
```

Server runs at **http://localhost:5000**

---

### STEP 3 — Open the Frontend

1. Open `web/static/index.html` in a browser
2. Or visit **http://localhost:5000** (Flask serves it automatically)
3. Enter student details and click **Assess Payment Risk**

> **Demo mode:** The frontend works without Flask running.
> It uses a local heuristic so you can test the UI immediately.
> To use the real ML model, set `DEMO_MODE = false` in `index.html`
> and start the Flask server.

---

## 🔌 API Reference

### POST /api/predict

**Request body (JSON):**
```json
{
  "payment_history":     12,
  "late_payments":        3,
  "outstanding_balance": 5000.00,
  "accommodation_type":  "shared",
  "monthly_income":      7500.00,
  "payment_trend":       "stable",
  "semester":             3,
  "length_of_stay":      12
}
```

**Response:**
```json
{
  "risk_label":    1,
  "risk_category": "High Risk",
  "confidence":    0.7842,
  "risk_factors":  ["High late payment count (7)", "Declining payment trend"],
  "timestamp":     "2025-01-15T14:32:00.123456"
}
```

### GET /api/health
```json
{"status": "ok", "models_loaded": true}
```

### GET /api/model-info
Returns model metadata and training logs.

---

## 📊 Dataset Features

| Feature | Type | Range | Description |
|---------|------|-------|-------------|
| `payment_history` | int | 0–24 | Number of on-time payments |
| `late_payments` | int | 0–12 | Number of late payments |
| `outstanding_balance` | float | 0–30,000 | Unpaid balance (ZAR) |
| `accommodation_type` | str | single/shared | Room type |
| `monthly_income` | float | 2,000–20,000 | Income estimate (ZAR) |
| `payment_trend` | str | increasing/stable/decreasing | Payment trend |
| `semester` | int | 1–8 | Current semester |
| `length_of_stay` | int | 1–48 | Months in accommodation |
| `risk_label` | int | 0 or 1 | **Target**: 0=Low, 1=High |

---

## 🤖 Models Compared

| Model | Typical Accuracy | Typical F1 | Notes |
|-------|-----------------|------------|-------|
| Logistic Regression | ~78–82% | ~0.77–0.81 | Fast, interpretable |
| Random Forest | ~85–89% | ~0.85–0.88 | Good baseline tree model |
| XGBoost (tuned) | ~87–92% | ~0.87–0.91 | **Best performer** |

---

## 🔑 Key Insights (from EDA)

1. **Late payments** is the strongest predictor of high risk
2. **Outstanding balance** strongly correlates with risk
3. **Monthly income** is inversely correlated with risk
4. Students with a **decreasing payment trend** are 3× more likely to be high-risk
5. **Single room** students face higher risk due to higher costs

---

## 💡 Tips for Google Colab

```python
# Download all outputs at once
from google.colab import files
import os, zipfile

# Zip all outputs
with zipfile.ZipFile('sams_outputs.zip', 'w') as zf:
    for f in os.listdir('.'):
        if f.endswith(('.pkl', '.csv', '.json', '.png')):
            zf.write(f)

files.download('sams_outputs.zip')
```

---

## 🚀 Next Improvements

- [ ] Add SHAP values for per-student explanations
- [ ] Build a student-facing dashboard (historical trend charts)
- [ ] Connect to a real PostgreSQL/MySQL database
- [ ] Add authentication to the API
- [ ] Deploy to Heroku, Railway, or AWS Elastic Beanstalk
- [ ] Schedule monthly model retraining


