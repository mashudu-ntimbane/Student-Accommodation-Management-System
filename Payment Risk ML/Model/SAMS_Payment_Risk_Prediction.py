# ============================================================
# SAMS - Student Accommodation Management System
# Payment Risk Prediction Model
# Google Colab Notebook
# ============================================================
# Run each section sequentially in Google Colab.
# Install required packages first if not already installed.
# ============================================================

# ----------------------------------------------------------
# SECTION 0: INSTALL DEPENDENCIES
# ----------------------------------------------------------
# !pip install xgboost scikit-learn pandas numpy matplotlib seaborn joblib flask -q

# ============================================================
# SECTION 1: IMPORT LIBRARIES
# ============================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
import time
import json
import os

# Scikit-learn modules
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,
    ConfusionMatrixDisplay
)
from sklearn.pipeline import Pipeline
import xgboost as xgb
import joblib

# Reproducibility
np.random.seed(42)
warnings.filterwarnings('ignore')

# Plot style
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12
sns.set_theme(style="whitegrid", palette="muted")

print("=" * 60)
print("  SAMS Payment Risk Prediction — Libraries Loaded ✓")
print("=" * 60)


# ============================================================
# SECTION 2: SYNTHETIC DATASET GENERATION
# ============================================================
# We generate 1000 realistic student records.
# Each feature is drawn from distributions that reflect
# real-world student payment behaviour.
# ============================================================

def generate_sams_dataset(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic SAMS dataset with realistic feature correlations.

    Parameters
    ----------
    n_samples : int
        Number of student records to generate.
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        A DataFrame with all required features and the risk_label target.
    """
    rng = np.random.default_rng(random_state)

    # --- Student IDs ---
    student_ids = [f"STU{str(i).zfill(4)}" for i in range(1, n_samples + 1)]

    # --- Accommodation type (single rooms cost more → higher risk) ---
    accommodation_type = rng.choice(
        ['single', 'shared'],
        size=n_samples,
        p=[0.40, 0.60]          # 40 % single, 60 % shared
    )
    is_single = (accommodation_type == 'single').astype(int)

    # --- Monthly income estimate (ZAR) ---
    # Single-room students tend to have slightly higher incomes
    monthly_income = (
        rng.normal(loc=8000, scale=2500, size=n_samples)
        + is_single * rng.normal(loc=1500, scale=500, size=n_samples)
    ).clip(2000, 20000).round(2)

    # --- Semester (1–8, representing academic progress) ---
    semester = rng.integers(1, 9, size=n_samples)

    # --- Length of stay (months, 1–48) ---
    length_of_stay = rng.integers(1, 49, size=n_samples)

    # --- Payment history: on-time payments (0–24) ---
    # Higher income and longer stay → more on-time payments
    payment_history_raw = (
        (monthly_income / 1000) * 1.2
        + length_of_stay * 0.3
        + rng.normal(0, 2, n_samples)
    )
    payment_history = payment_history_raw.clip(0, 24).round().astype(int)

    # --- Late payments (0–12) ---
    # Inversely correlated with payment history and income
    late_payments_raw = (
        12 - payment_history * 0.5
        + is_single * 2
        - (monthly_income / 5000)
        + rng.normal(0, 1.5, n_samples)
    )
    late_payments = late_payments_raw.clip(0, 12).round().astype(int)

    # --- Outstanding balance (ZAR, 0–30 000) ---
    # More late payments → higher outstanding balance
    outstanding_balance = (
        late_payments * 1200
        + is_single * 2500
        - monthly_income * 0.15
        + rng.normal(0, 1000, n_samples)
    ).clip(0, 30000).round(2)

    # --- Payment trend ---
    # Students with many late payments are more likely to be "decreasing"
    trend_probs = np.where(
        late_payments > 4,
        [0.15, 0.55, 0.30],   # mostly decreasing
        [0.45, 0.15, 0.40]    # mostly increasing/stable
    )
    payment_trend = np.array([
        rng.choice(['increasing', 'decreasing', 'stable'], p=trend_probs[i])
        for i in range(n_samples)
    ])

    # --- Risk label (target) ---
    # Derived from a weighted combination of risk factors
    risk_score = (
        late_payments * 0.40
        + outstanding_balance / 5000 * 0.25
        + (payment_history * -0.20)
        + is_single * 0.10
        + (monthly_income / 20000 * -0.15)
        + (payment_trend == 'decreasing').astype(int) * 0.20
        + rng.normal(0, 0.1, n_samples)  # small noise
    )
    # Normalise to [0, 1] and threshold at 0.5
    risk_score_norm = (risk_score - risk_score.min()) / (risk_score.max() - risk_score.min())
    risk_label = (risk_score_norm >= 0.50).astype(int)

    df = pd.DataFrame({
        'student_id':          student_ids,
        'payment_history':     payment_history,
        'late_payments':       late_payments,
        'outstanding_balance': outstanding_balance,
        'accommodation_type':  accommodation_type,
        'monthly_income':      monthly_income,
        'payment_trend':       payment_trend,
        'semester':            semester,
        'length_of_stay':      length_of_stay,
        'risk_label':          risk_label
    })

    return df


# Generate the dataset
df = generate_sams_dataset(n_samples=1000)

print(f"\n✓ Dataset generated: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"\nClass distribution (risk_label):")
print(df['risk_label'].value_counts().rename({0: 'Low Risk (0)', 1: 'High Risk (1)'}))
print(f"\nClass balance: {df['risk_label'].mean():.1%} high-risk students")
print("\nFirst 5 records:")
print(df.head())

# Save raw dataset
df.to_csv('sams_dataset.csv', index=False)
print("\n✓ Dataset saved → sams_dataset.csv")


# ============================================================
# SECTION 3: DATA PREPROCESSING
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 3: DATA PREPROCESSING")
print("=" * 60)

# --- 3.1 Missing value check ---
print("\n[3.1] Missing values per column:")
print(df.isnull().sum())

# --- 3.2 Basic statistics ---
print("\n[3.2] Descriptive statistics (numerical features):")
print(df.describe().round(2))

# --- 3.3 Encode categorical features ---
# LabelEncoder converts string categories to integers
le_accommodation = LabelEncoder()
le_trend = LabelEncoder()

df_encoded = df.copy()
df_encoded['accommodation_type'] = le_accommodation.fit_transform(df['accommodation_type'])
df_encoded['payment_trend']      = le_trend.fit_transform(df['payment_trend'])

print("\n[3.3] Categorical encoding mapping:")
print("  accommodation_type :", dict(zip(le_accommodation.classes_, le_accommodation.transform(le_accommodation.classes_))))
print("  payment_trend      :", dict(zip(le_trend.classes_, le_trend.transform(le_trend.classes_))))

# --- 3.4 Feature matrix and target vector ---
FEATURE_COLS = [
    'payment_history', 'late_payments', 'outstanding_balance',
    'accommodation_type', 'monthly_income', 'payment_trend',
    'semester', 'length_of_stay'
]
TARGET_COL = 'risk_label'

X = df_encoded[FEATURE_COLS]
y = df_encoded[TARGET_COL]

# --- 3.5 Train / Test split (80 / 20, stratified) ---
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n[3.5] Train size: {X_train.shape[0]} | Test size: {X_test.shape[0]}")

# --- 3.6 Feature scaling (StandardScaler) ---
# Logistic Regression is sensitive to scale; tree models are not,
# but scaling helps compare models on the same footing.
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

print("\n[3.6] Features scaled with StandardScaler ✓")
print(f"  Mean (first feature after scaling): {X_train_scaled[:, 0].mean():.4f}")
print(f"  Std  (first feature after scaling): {X_train_scaled[:, 0].std():.4f}")


# ============================================================
# SECTION 4: EXPLORATORY DATA ANALYSIS (EDA)
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 4: EXPLORATORY DATA ANALYSIS")
print("=" * 60)

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('SAMS — EDA: Feature Distributions by Risk Label', fontsize=16, fontweight='bold')

palette = {0: '#2196F3', 1: '#F44336'}
labels  = {0: 'Low Risk', 1: 'High Risk'}

# Plot 1: Late payments distribution
sns.histplot(data=df, x='late_payments', hue='risk_label', bins=12,
             palette=palette, ax=axes[0, 0], kde=True)
axes[0, 0].set_title('Late Payments Distribution')
axes[0, 0].set_xlabel('Number of Late Payments')

# Plot 2: Outstanding balance boxplot
sns.boxplot(data=df, x='risk_label', y='outstanding_balance',
            palette=palette, ax=axes[0, 1])
axes[0, 1].set_title('Outstanding Balance by Risk')
axes[0, 1].set_xticklabels(['Low Risk', 'High Risk'])

# Plot 3: Monthly income boxplot
sns.boxplot(data=df, x='risk_label', y='monthly_income',
            palette=palette, ax=axes[0, 2])
axes[0, 2].set_title('Monthly Income by Risk')
axes[0, 2].set_xticklabels(['Low Risk', 'High Risk'])

# Plot 4: Payment trend counts
trend_counts = df.groupby(['payment_trend', 'risk_label']).size().reset_index(name='count')
sns.barplot(data=trend_counts, x='payment_trend', y='count',
            hue='risk_label', palette=palette, ax=axes[1, 0])
axes[1, 0].set_title('Payment Trend vs Risk Label')
axes[1, 0].legend(title='Risk', labels=['Low Risk', 'High Risk'])

# Plot 5: Accommodation type counts
acc_counts = df.groupby(['accommodation_type', 'risk_label']).size().reset_index(name='count')
sns.barplot(data=acc_counts, x='accommodation_type', y='count',
            hue='risk_label', palette=palette, ax=axes[1, 1])
axes[1, 1].set_title('Accommodation Type vs Risk Label')
axes[1, 1].legend(title='Risk', labels=['Low Risk', 'High Risk'])

# Plot 6: Risk label distribution pie
risk_counts = df['risk_label'].value_counts()
axes[1, 2].pie(risk_counts, labels=['Low Risk', 'High Risk'],
               autopct='%1.1f%%', colors=['#2196F3', '#F44336'],
               startangle=90, explode=(0.05, 0.05))
axes[1, 2].set_title('Overall Risk Label Distribution')

plt.tight_layout()
plt.savefig('eda_distributions.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n✓ EDA plot saved → eda_distributions.png")

# --- Correlation heatmap ---
fig, ax = plt.subplots(figsize=(10, 8))
corr_matrix = df_encoded[FEATURE_COLS + [TARGET_COL]].corr()
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdYlGn_r',
            mask=mask, ax=ax, linewidths=0.5, vmin=-1, vmax=1)
ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig('eda_correlation.png', dpi=150, bbox_inches='tight')
plt.show()
print("✓ Correlation heatmap saved → eda_correlation.png")

# --- Key EDA Insights ---
print("\n[KEY EDA INSIGHTS]")
print(f"  • Avg late payments  — Low Risk: {df[df.risk_label==0].late_payments.mean():.1f} | High Risk: {df[df.risk_label==1].late_payments.mean():.1f}")
print(f"  • Avg balance        — Low Risk: R{df[df.risk_label==0].outstanding_balance.mean():,.0f} | High Risk: R{df[df.risk_label==1].outstanding_balance.mean():,.0f}")
print(f"  • Avg monthly income — Low Risk: R{df[df.risk_label==0].monthly_income.mean():,.0f} | High Risk: R{df[df.risk_label==1].monthly_income.mean():,.0f}")


# ============================================================
# SECTION 5: MODEL BUILDING & TRAINING
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 5: MODEL BUILDING & TRAINING")
print("=" * 60)

# Training log container
training_logs = {}

def train_and_log(name, model, X_tr, y_tr, X_te, y_te, use_scaled=True):
    """
    Train a model, evaluate it, and log results.

    Parameters
    ----------
    name        : str   — Model name
    model       : estimator
    X_tr, y_tr  : training data
    X_te, y_te  : test data
    use_scaled  : bool  — use scaled features (for LogReg)

    Returns
    -------
    dict with metrics
    """
    Xtr = X_tr if not use_scaled else X_train_scaled
    Xte = X_te if not use_scaled else X_test_scaled

    t0 = time.time()
    model.fit(Xtr, y_tr)
    train_time = time.time() - t0

    y_pred = model.predict(Xte)
    y_prob = model.predict_proba(Xte)[:, 1]

    acc  = accuracy_score(y_te, y_pred)
    prec = precision_score(y_te, y_pred)
    rec  = recall_score(y_te, y_pred)
    f1   = f1_score(y_te, y_pred)
    fpr, tpr, _ = roc_curve(y_te, y_prob)
    roc_auc = auc(fpr, tpr)

    log = {
        'model':       name,
        'accuracy':    round(acc, 4),
        'precision':   round(prec, 4),
        'recall':      round(rec, 4),
        'f1_score':    round(f1, 4),
        'roc_auc':     round(roc_auc, 4),
        'train_time_s': round(train_time, 4),
        'fpr':         fpr.tolist(),
        'tpr':         tpr.tolist(),
        'y_pred':      y_pred.tolist(),
        'y_prob':      y_prob.tolist()
    }

    print(f"\n  ── {name} ──")
    print(f"    Accuracy : {acc:.4f}")
    print(f"    Precision: {prec:.4f}")
    print(f"    Recall   : {rec:.4f}")
    print(f"    F1-Score : {f1:.4f}")
    print(f"    ROC-AUC  : {roc_auc:.4f}")
    print(f"    Train time: {train_time:.3f}s")
    print(f"\n    Classification Report:\n")
    print(classification_report(y_te, y_pred, target_names=['Low Risk', 'High Risk']))

    return log, model

# ----- MODEL 1: Logistic Regression -----
print("\n[5.1] Training Logistic Regression...")
lr_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
lr_log, lr_model = train_and_log(
    'Logistic Regression', lr_model,
    X_train_scaled, y_train, X_test_scaled, y_test, use_scaled=False
)
training_logs['logistic_regression'] = lr_log

# ----- MODEL 2: Random Forest -----
print("\n[5.2] Training Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=200, max_depth=8, min_samples_split=5,
    random_state=42, class_weight='balanced', n_jobs=-1
)
rf_log, rf_model = train_and_log(
    'Random Forest', rf_model,
    X_train, y_train, X_test, y_test, use_scaled=False
)
training_logs['random_forest'] = rf_log

# ----- MODEL 3: XGBoost -----
print("\n[5.3] Training XGBoost...")
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
xgb_model = xgb.XGBClassifier(
    n_estimators=200, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=scale_pos_weight,
    use_label_encoder=False, eval_metric='logloss',
    random_state=42, n_jobs=-1
)
xgb_log, xgb_model = train_and_log(
    'XGBoost', xgb_model,
    X_train, y_train, X_test, y_test, use_scaled=False
)
training_logs['xgboost'] = xgb_log


# ============================================================
# SECTION 6: MODEL EVALUATION & VISUALISATION
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 6: MODEL EVALUATION")
print("=" * 60)

models_info = [
    ('Logistic Regression', lr_log,  lr_model,  X_test_scaled),
    ('Random Forest',       rf_log,  rf_model,  X_test),
    ('XGBoost',             xgb_log, xgb_model, X_test),
]

# --- 6.1 Confusion Matrices ---
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('SAMS — Confusion Matrices', fontsize=15, fontweight='bold')

for ax, (name, log, model, X_te) in zip(axes, models_info):
    y_pred = model.predict(X_te)
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Low Risk', 'High Risk'])
    disp.plot(ax=ax, colorbar=False, cmap='Blues')
    ax.set_title(name, fontsize=12)

plt.tight_layout()
plt.savefig('confusion_matrices.png', dpi=150, bbox_inches='tight')
plt.show()
print("✓ Confusion matrices saved → confusion_matrices.png")

# --- 6.2 ROC Curves ---
fig, ax = plt.subplots(figsize=(9, 7))
colors = ['#1565C0', '#2E7D32', '#BF360C']

for (name, log, model, _), color in zip(models_info, colors):
    ax.plot(log['fpr'], log['tpr'],
            label=f"{name} (AUC = {log['roc_auc']:.3f})",
            color=color, lw=2)

ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Random Classifier')
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('ROC Curves — All Models', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('roc_curves.png', dpi=150, bbox_inches='tight')
plt.show()
print("✓ ROC curves saved → roc_curves.png")

# --- 6.3 Performance Summary Bar Chart ---
metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'roc_auc']
model_names = ['Logistic Reg.', 'Random Forest', 'XGBoost']
logs_list = [lr_log, rf_log, xgb_log]

x = np.arange(len(metrics))
width = 0.25
fig, ax = plt.subplots(figsize=(13, 6))
colors_bar = ['#1565C0', '#2E7D32', '#BF360C']

for i, (log, mname, color) in enumerate(zip(logs_list, model_names, colors_bar)):
    vals = [log[m] for m in metrics]
    bars = ax.bar(x + i * width, vals, width, label=mname, color=color, alpha=0.85)
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f'{bar.get_height():.3f}', ha='center', va='bottom', fontsize=8)

ax.set_xlabel('Metric', fontsize=12)
ax.set_ylabel('Score', fontsize=12)
ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
ax.set_xticks(x + width)
ax.set_xticklabels(['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC'], fontsize=11)
ax.set_ylim(0, 1.1)
ax.legend(fontsize=11)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('model_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print("✓ Model comparison chart saved → model_comparison.png")


# ============================================================
# SECTION 7: FEATURE IMPORTANCE
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 7: FEATURE IMPORTANCE")
print("=" * 60)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle('Feature Importance — Random Forest vs XGBoost', fontsize=14, fontweight='bold')

feature_names = FEATURE_COLS

# Random Forest importances
rf_imp = pd.Series(rf_model.feature_importances_, index=feature_names).sort_values(ascending=True)
rf_imp.plot(kind='barh', ax=axes[0], color='#2E7D32', alpha=0.85)
axes[0].set_title('Random Forest', fontsize=12)
axes[0].set_xlabel('Feature Importance (Gini)')
for i, v in enumerate(rf_imp):
    axes[0].text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=9)

# XGBoost importances
xgb_imp = pd.Series(xgb_model.feature_importances_, index=feature_names).sort_values(ascending=True)
xgb_imp.plot(kind='barh', ax=axes[1], color='#BF360C', alpha=0.85)
axes[1].set_title('XGBoost', fontsize=12)
axes[1].set_xlabel('Feature Importance (Gain)')
for i, v in enumerate(xgb_imp):
    axes[1].text(v + 0.002, i, f'{v:.3f}', va='center', fontsize=9)

plt.tight_layout()
plt.savefig('feature_importance.png', dpi=150, bbox_inches='tight')
plt.show()
print("✓ Feature importance chart saved → feature_importance.png")

print("\n[TOP 3 FEATURES — Random Forest]")
for feat, imp in rf_imp.sort_values(ascending=False).head(3).items():
    print(f"  • {feat}: {imp:.4f}")

print("\n[TOP 3 FEATURES — XGBoost]")
for feat, imp in xgb_imp.sort_values(ascending=False).head(3).items():
    print(f"  • {feat}: {imp:.4f}")


# ============================================================
# SECTION 8: HYPERPARAMETER TUNING & CROSS-VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 8: HYPERPARAMETER TUNING")
print("=" * 60)

# --- 8.1 Cross-validation on best candidate (XGBoost) ---
print("\n[8.1] Stratified 5-Fold Cross-Validation (XGBoost)...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=cv, scoring='f1', n_jobs=-1)
print(f"  CV F1 Scores : {cv_scores.round(4)}")
print(f"  Mean F1      : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Log CV results
training_logs['xgboost']['cv_f1_scores'] = cv_scores.tolist()
training_logs['xgboost']['cv_f1_mean']   = round(cv_scores.mean(), 4)
training_logs['xgboost']['cv_f1_std']    = round(cv_scores.std(), 4)

# --- 8.2 GridSearchCV for XGBoost ---
print("\n[8.2] GridSearchCV on XGBoost (this may take a minute)...")
param_grid = {
    'n_estimators':  [100, 200],
    'max_depth':     [4, 6],
    'learning_rate': [0.05, 0.10],
}

grid_search = GridSearchCV(
    xgb.XGBClassifier(
        subsample=0.8, colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False, eval_metric='logloss',
        random_state=42, n_jobs=-1
    ),
    param_grid, cv=3, scoring='f1', n_jobs=-1, verbose=0
)
grid_search.fit(X_train, y_train)

print(f"  Best params : {grid_search.best_params_}")
print(f"  Best CV F1  : {grid_search.best_score_:.4f}")

# Re-evaluate best model on test set
best_xgb = grid_search.best_estimator_
y_pred_best = best_xgb.predict(X_test)
f1_best = f1_score(y_test, y_pred_best)
acc_best = accuracy_score(y_test, y_pred_best)
print(f"  Test Accuracy (tuned): {acc_best:.4f}")
print(f"  Test F1-Score (tuned): {f1_best:.4f}")

training_logs['xgboost_tuned'] = {
    'best_params': grid_search.best_params_,
    'best_cv_f1':  round(grid_search.best_score_, 4),
    'test_accuracy': round(acc_best, 4),
    'test_f1':       round(f1_best, 4)
}


# ============================================================
# SECTION 9: SAVE TRAINING LOGS & MODELS
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 9: SAVING MODELS & LOGS")
print("=" * 60)

# --- Remove non-serialisable lists before saving JSON ---
logs_to_save = {}
for k, v in training_logs.items():
    logs_to_save[k] = {k2: v2 for k2, v2 in v.items()
                       if not isinstance(v2, list) or k2 in ['cv_f1_scores']}

with open('training_logs.json', 'w') as f:
    json.dump(logs_to_save, f, indent=4, default=str)
print("✓ Training logs saved → training_logs.json")

# Save models and preprocessors
joblib.dump(best_xgb,           'sams_xgb_model.pkl')
joblib.dump(rf_model,           'sams_rf_model.pkl')
joblib.dump(lr_model,           'sams_lr_model.pkl')
joblib.dump(scaler,             'sams_scaler.pkl')
joblib.dump(le_accommodation,   'sams_le_accommodation.pkl')
joblib.dump(le_trend,           'sams_le_trend.pkl')

print("✓ Models saved:")
print("   sams_xgb_model.pkl  (primary / best model)")
print("   sams_rf_model.pkl")
print("   sams_lr_model.pkl")
print("✓ Preprocessors saved:")
print("   sams_scaler.pkl")
print("   sams_le_accommodation.pkl")
print("   sams_le_trend.pkl")


# ============================================================
# SECTION 10: PREDICTION FUNCTION (FOR DEPLOYMENT)
# ============================================================

print("\n" + "=" * 60)
print("  SECTION 10: PREDICTION FUNCTION")
print("=" * 60)

def predict_payment_risk(
    payment_history: int,
    late_payments: int,
    outstanding_balance: float,
    accommodation_type: str,       # 'single' or 'shared'
    monthly_income: float,
    payment_trend: str,            # 'increasing', 'decreasing', 'stable'
    semester: int,
    length_of_stay: int,
    model=None,
    scaler_obj=None,
    le_acc=None,
    le_tr=None
) -> dict:
    """
    Predict payment risk for a single student record.

    Returns a dictionary with:
    - risk_label    : 0 (low) or 1 (high)
    - risk_category : 'Low Risk' or 'High Risk'
    - confidence    : probability of being high risk (0–1)
    - risk_factors  : list of contributing factors
    """
    if model is None:
        model = best_xgb
    if scaler_obj is None:
        scaler_obj = scaler
    if le_acc is None:
        le_acc = le_accommodation
    if le_tr is None:
        le_tr = le_trend

    # Encode categoricals
    acc_encoded   = le_acc.transform([accommodation_type])[0]
    trend_encoded = le_tr.transform([payment_trend])[0]

    # Build feature row
    features = np.array([[
        payment_history, late_payments, outstanding_balance,
        acc_encoded, monthly_income, trend_encoded,
        semester, length_of_stay
    ]])

    # Predict
    prob  = model.predict_proba(features)[0][1]
    label = int(prob >= 0.50)

    # Human-readable risk factors
    risk_factors = []
    if late_payments > 4:
        risk_factors.append(f"High late payment count ({late_payments})")
    if outstanding_balance > 8000:
        risk_factors.append(f"Large outstanding balance (R{outstanding_balance:,.0f})")
    if monthly_income < 5000:
        risk_factors.append("Low monthly income")
    if payment_trend == 'decreasing':
        risk_factors.append("Declining payment trend")
    if accommodation_type == 'single':
        risk_factors.append("Single room (higher cost)")
    if not risk_factors:
        risk_factors = ['No significant risk factors identified']

    return {
        'risk_label':    label,
        'risk_category': 'High Risk' if label == 1 else 'Low Risk',
        'confidence':    round(float(prob), 4),
        'risk_factors':  risk_factors
    }


# --- Demo prediction ---
print("\nDemo prediction for a sample student:")
result = predict_payment_risk(
    payment_history    = 3,
    late_payments      = 7,
    outstanding_balance= 12000,
    accommodation_type = 'single',
    monthly_income     = 4500,
    payment_trend      = 'decreasing',
    semester           = 3,
    length_of_stay     = 12
)
print(f"  Risk Category : {result['risk_category']}")
print(f"  Confidence    : {result['confidence']:.1%}")
print(f"  Risk Factors  : {', '.join(result['risk_factors'])}")

print("\n" + "=" * 60)
print("  ✅ SAMS ML PIPELINE COMPLETE")
print("=" * 60)
print("""
Files generated:
  📄 sams_dataset.csv            — Synthetic training data
  📄 training_logs.json          — All metrics & CV results
  🖼  eda_distributions.png      — EDA plots
  🖼  eda_correlation.png        — Correlation heatmap
  🖼  confusion_matrices.png     — All 3 model confusion matrices
  🖼  roc_curves.png             — ROC curves comparison
  🖼  model_comparison.png       — Metric bar chart
  🖼  feature_importance.png     — RF & XGBoost importances
  🤖 sams_xgb_model.pkl         — Best model (XGBoost tuned)
  🤖 sams_rf_model.pkl
  🤖 sams_lr_model.pkl
  🔧 sams_scaler.pkl
  🔧 sams_le_accommodation.pkl
  🔧 sams_le_trend.pkl

Next step → run the Flask API (app.py) and open index.html
""")
