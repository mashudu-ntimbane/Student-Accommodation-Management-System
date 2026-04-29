"""
SAMS — Payment Risk Prediction API
Flask backend that loads the trained XGBoost model and serves predictions.

Usage:
    pip install flask flask-cors joblib scikit-learn xgboost numpy
    python app.py

Then open http://localhost:5000 in your browser.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import numpy as np
import joblib
import os
import json
from datetime import datetime

# ── Load model artefacts ──────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR   = os.path.join(BASE_DIR, 'models')   # put .pkl files here

def load_artefact(filename):
    """Load a joblib artefact from the models/ directory."""
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Artefact '{filename}' not found in {MODEL_DIR}.\n"
            "Please run the Colab notebook first and copy the .pkl files into the models/ folder."
        )
    return joblib.load(path)

try:
    model            = load_artefact('sams_xgb_model.pkl')
    scaler           = load_artefact('sams_scaler.pkl')
    le_accommodation = load_artefact('sams_le_accommodation.pkl')
    le_trend         = load_artefact('sams_le_trend.pkl')
    MODELS_LOADED    = True
    print("✓ All model artefacts loaded successfully.")
except FileNotFoundError as e:
    print(f"⚠  {e}")
    MODELS_LOADED = False


# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)   # allow cross-origin requests (for development)


# ── Helper: risk prediction ───────────────────────────────────────────────────
def predict_risk(data: dict) -> dict:
    """
    Core prediction function.

    Parameters
    ----------
    data : dict with keys matching the form fields.

    Returns
    -------
    dict with risk_label, risk_category, confidence, risk_factors.
    """
    if not MODELS_LOADED:
        return {
            'error': 'Model artefacts not loaded. Run the Colab notebook first.',
            'demo_mode': True,
            'risk_label':    1,
            'risk_category': 'High Risk (DEMO)',
            'confidence':    0.82,
            'risk_factors':  ['Running in demo mode — no model files found']
        }

    payment_history     = int(data['payment_history'])
    late_payments       = int(data['late_payments'])
    outstanding_balance = float(data['outstanding_balance'])
    accommodation_type  = str(data['accommodation_type'])
    monthly_income      = float(data['monthly_income'])
    payment_trend       = str(data['payment_trend'])
    semester            = int(data['semester'])
    length_of_stay      = int(data['length_of_stay'])

    # Validate categorical values
    if accommodation_type not in le_accommodation.classes_:
        raise ValueError(f"Invalid accommodation_type: {accommodation_type}")
    if payment_trend not in le_trend.classes_:
        raise ValueError(f"Invalid payment_trend: {payment_trend}")

    acc_encoded   = le_accommodation.transform([accommodation_type])[0]
    trend_encoded = le_trend.transform([payment_trend])[0]

    features = np.array([[
        payment_history, late_payments, outstanding_balance,
        acc_encoded, monthly_income, trend_encoded,
        semester, length_of_stay
    ]])

    prob  = float(model.predict_proba(features)[0][1])
    label = int(prob >= 0.50)

    # Risk factor explanations
    risk_factors = []
    if late_payments >= 5:
        risk_factors.append(f"High number of late payments ({late_payments})")
    if outstanding_balance > 8000:
        risk_factors.append(f"Large outstanding balance (R{outstanding_balance:,.0f})")
    if monthly_income < 5000:
        risk_factors.append(f"Low monthly income estimate (R{monthly_income:,.0f})")
    if payment_trend == 'decreasing':
        risk_factors.append("Payment trend is declining")
    if accommodation_type == 'single':
        risk_factors.append("Single room accommodation (higher cost)")
    if payment_history < 5:
        risk_factors.append("Limited on-time payment history")
    if not risk_factors:
        risk_factors = ['No major risk factors identified']

    return {
        'risk_label':    label,
        'risk_category': 'High Risk' if label == 1 else 'Low Risk',
        'confidence':    round(prob, 4),
        'risk_factors':  risk_factors,
        'timestamp':     datetime.now().isoformat()
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    """Serve the main frontend page."""
    return send_from_directory('static', 'index.html')


@app.route('/api/predict', methods=['POST'])
def predict():
    """
    POST /api/predict
    Body: JSON with student features
    Returns: JSON prediction result
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'No JSON body received.'}), 400

        required = [
            'payment_history', 'late_payments', 'outstanding_balance',
            'accommodation_type', 'monthly_income', 'payment_trend',
            'semester', 'length_of_stay'
        ]
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({'error': f"Missing fields: {missing}"}), 400

        result = predict_risk(data)
        return jsonify(result), 200

    except ValueError as ve:
        return jsonify({'error': str(ve)}), 422
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health-check endpoint."""
    return jsonify({
        'status':       'ok',
        'models_loaded': MODELS_LOADED,
        'timestamp':    datetime.now().isoformat()
    })


@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Return basic model metadata."""
    info = {
        'model_type':   'XGBoost Classifier (hyperparameter-tuned)',
        'features':     [
            'payment_history', 'late_payments', 'outstanding_balance',
            'accommodation_type', 'monthly_income', 'payment_trend',
            'semester', 'length_of_stay'
        ],
        'target':       'risk_label (0 = Low Risk, 1 = High Risk)',
        'models_loaded': MODELS_LOADED
    }
    # Attach training logs if available
    log_path = os.path.join(MODEL_DIR, 'training_logs.json')
    if os.path.exists(log_path):
        with open(log_path) as f:
            info['training_logs'] = json.load(f)
    return jsonify(info)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("\n" + "=" * 55)
    print("  SAMS Payment Risk Prediction API")
    print("  http://localhost:5000")
    print("=" * 55 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
