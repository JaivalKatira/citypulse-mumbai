# CityPulse Mumbai: Reproducibility & Judge Evaluation Guide
**HackAMatch 1.0 — Data Science + AI Challenge**  
**Track:** Urban Computing & AI Decision Support  
**Official Rule Compliance:** Section 4 & 11 (Zero-Cost, Public Data, Free-Tier Reproducibility)  

---

## 1. Quick Verification (One-Command Launch)

Judges can launch and test the full application locally in under 60 seconds with **zero paid keys, zero credit cards, and zero proprietary dependencies**.

### Prerequisites
- Node.js (v18+) & npm
- Python (3.10+) with `pandas`, `scikit-learn`, `scipy`

### Step 1: Clone & Install
```bash
# Clone the repository
git clone <REPO_URL>
cd CityPulse

# Install frontend dependencies
cd client
npm install
```

### Step 2: Start the Modern Decision Cockpit
```bash
# Run local dev server
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 2. Re-Running the Analytical & ML Pipeline (Optional)

To verify that the dataset, feature engineering, and model benchmark are genuine and fully reproducible from raw records:

```bash
# In the repository root
py data_pipeline.py
# (or 'python3 data_pipeline.py' on Linux/macOS)
```

**Expected Console Output:**
```text
Loaded raw dataset: 538 records, 18 columns.
Missing values audit: 0 total nulls across dataset.

--- RUNNING STATISTICAL EDA & EXTRACTING 3 ACTIONABLE FINDINGS ---

--- TRAINING & VALIDATING MODELS WITH OUT-OF-SAMPLE CROSS-VALIDATION ---
Baseline Metrics: {'mae': 0.394, 'rmse': 0.512, 'r2': 0.994, 'spearman_rho': 0.996}
Ridge Regressor Metrics: {'mae': 0.013, 'rmse': 0.018, 'r2': 1.0, 'spearman_rho': 1.0}
Random Forest Regressor Metrics: {'mae': 0.245, 'rmse': 0.356, 'r2': 0.997, 'spearman_rho': 0.998}

--- EXPORTING CURATED JSON FOR WEB APPLICATION ---
Successfully exported curated data to client/public/data/citypulse_mumbai_curated.json
Saved cleaned benchmark CSV to citypulse_mumbai_cleaned.csv
```

---

## 3. Compliance Verification Checklist for Technical Judges

- [x] **Zero Paid APIs:** Uses OpenStreetMap (ODbL) and CartoDB Dark Matter public tiles. No Google Maps, Mapbox, or OpenAI paid billing keys required.
- [x] **Zero Data Leakage:** 20% holdout split stratified by risk severity; scalers and model estimators fitted strictly on training partition.
- [x] **Benchmark Baseline Included:** Naive Crime-Population heuristic formally compared against Ridge and Random Forest models.
- [x] **Decision Support vs. Data Display:** Features a live **What-If Policy Simulator** allowing dynamic recalculation of risk scores under varying municipal investments.
- [x] **Uncertainty & Explainability:** Every locality displays 95% Confidence Intervals and SHAP-inspired factor attribution bars.
- [x] **Responsible AI Compliance:** Prominent disclaimers regarding prototype status, reporting friction bias, and correlation vs. causation.
