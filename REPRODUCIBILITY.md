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

## 2. Re-Running the Analytical Pipeline (Optional)

To verify the analytical calculations, formula reverse-engineering, and benchmark baseline from raw records:

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

--- DECOMPOSING FORMULA-DERIVED COMPOSITE INDICATOR & BENCHMARKING ---
Index Decomposition R^2: 1.00000000 (Max absolute residual: 8.86e-12)
Exact Formula: risk_index = 6.2726 + 0.1136*crimes - 0.000072*pop_dense + 0.4013*pol_dense + 0.9224*uhi - 0.0870*internet
Naive Per-Capita Baseline Metrics: {'mae': 2.283, 'rmse': 3.23, 'r2': 0.754, 'spearman_rho': 0.879}
Composite Indicator Fidelity Metrics: {'mae': 0.0, 'rmse': 0.0, 'r2': 1.0, 'spearman_rho': 1.0}

--- EXPORTING CURATED JSON FOR WEB APPLICATION ---
Successfully exported curated data to client/public/data/citypulse_mumbai_curated.json
Saved cleaned benchmark CSV to citypulse_mumbai_cleaned.csv
```

---

## 3. Compliance Verification Checklist for Technical Judges

- [x] **Zero Paid APIs:** Uses OpenStreetMap (ODbL) and CartoDB Dark Matter public tiles. No Google Maps, Mapbox, or OpenAI paid billing keys required.
- [x] **Analytical Integrity:** Avoids circular 99.7% ML claims by mathematically decomposing the composite indicator formula ($R^2=1.000$) and benchmarking it against an independent Naive baseline ($R^2=0.754, \rho=0.879$).
- [x] **Benchmark Baseline Included:** Transparent Naive Per-Capita Crime baseline ($\text{crimes}/\text{pop} \times 10,000$) formally benchmarked against the multi-criteria indicator.
- [x] **Decision Support vs. Data Display:** Features an interactive **Municipal Planning Scenario Explorer** allowing heuristic sensitivity testing of capital outlays (auxiliary chowkis, smart LED lighting).
- [x] **Uncertainty & Explainability:** Every locality displays an analytical 95% Confidence Interval ($\pm 0.70$) and closed-form factor attribution bars.
- [x] **Responsible AI & Provenance Disclaimers:** Prominent emergency disclaimers (Police 100/112, Women Helpline 1091), hypothetical simulator labels, reporting friction bias analysis, and clear distinction between traceable OSM entities and demonstration compilation records.
