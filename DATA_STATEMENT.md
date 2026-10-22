# CityPulse Mumbai: Data Statement & Provenance Specification
**Document Version:** 2.0 (Post-Audit Integrity Aligned)  
**Project:** CityPulse Mumbai — Urban Safety Vulnerability & Municipal Resource Allocation DSS  
**Challenge:** HackAMatch 1.0 — Data Science + AI Challenge  

---

## 1. Dataset Overview & Provenance Classification

- **Dataset Title:** Greater Mumbai Locality-Level Safety Risk, Infrastructure & Demographics Demonstration Dataset
- **Geographic Extent:** Greater Mumbai (Island City, Western Suburbs, Eastern Suburbs)
  - Latitude: 18.89°N to 19.28°N
  - Longitude: 72.78°E to 72.98°E
- **Temporal Scope:** Consolidated municipal administrative snapshot and OpenStreetMap live infrastructure pulls.
- **Total Records:** $N = 538$ distinct spatial observation units.
- **Access & Reproducibility:** 100% public, open data with zero-cost OpenStreetMap (Overpass API) geometries and CartoDB Dark Matter raster tiles. Zero paid API keys.

### Critical Classification: Traceable Facts vs. Demonstration Data
To uphold complete scientific integrity:

1. **Documented & Traceable Geospatial Entities:**
   - **Police Stations & Outposts:** Traceable to OpenStreetMap live infrastructure queries (`amenity=police`).
   - **Geocoding & Spatial Boundaries:** Coordinates, ward assignments, and macro-zones correspond to authentic Greater Mumbai geography.
2. **Compilation / Demonstration Data:**
   - **Observation Unit Heterogeneity:** The 538 records mix street segments (e.g., *Aloysius Soares Road*, *Dr. M.B. Velkar Street*), neighborhoods (*Bandra*, *Kurla*), and municipal wards (*"L" Ward*).
   - **Crime & Population Granularity:** Official Indian authorities (National Crime Records Bureau, Mumbai Police, MCGM) publish official crime and census records at ward or police station jurisdiction levels, not at individual street-segment levels. Consequently, the street-level crime counts and population figures in this dataset function as an open research and prototype compilation designed for municipal spatial decision-support demonstration.
   - **Target Variable (`risk_index`):** As proven through OLS decomposition, `risk_index` is a deterministic, formula-derived composite indicator. It is an existing multi-criteria priority scale (0–30), not an independently validated empirical measure of real-world crime outcomes.

---

## 2. Source Provenance & Licensing

| Component | Source Portal / Authority | License / Access Terms | Status & Verification |
| :--- | :--- | :--- | :--- |
| **Locality Demographics & Incident Compilation** | Municipal/research compilation adapted from open Mumbai safety research repository. | Open Public Research License | Traceable compilation; demonstration units. |
| **Police Station Geometries** | OpenStreetMap (OSM) via Overpass API (`amenity=police`). | Open Database License (ODbL) © OpenStreetMap contributors | Verified live geometries; zero paid keys. |
| **Geocoding & Centroids** | OpenStreetMap Nominatim with Mumbai bounding box constraints. | ODbL / OSM Foundation Acceptable Use | Verified coordinates. |
| **Basemap Tiles** | CartoDB Dark Matter free public raster tiles. | © OpenStreetMap contributors, © CARTO | Free public raster endpoint. |

---

## 3. Data Dictionary & Schema

The curated dataset contains 538 rows and 22 curated attributes:

| Variable Name | Data Type | Units / Range | Definition & Context |
| :--- | :--- | :--- | :--- |
| `locality` | String | Categorical | Locality name in Mumbai (street, neighborhood, or ward level). |
| `zone` | String | Categorical | Macro-administrative zone: *Island City*, *Western Suburbs*, or *Eastern Suburbs*. |
| `ward` | String | Categorical | Brihanmumbai Municipal Corporation (BMC) administrative ward. |
| `lat`, `lon` | Float | Decimal Degrees | Geographic centroid coordinates. |
| `population` | Integer | $5,600 - 32,000$ | Resident population figure in demonstration record. |
| `area_sq_km` | Float | $0.35 - 1.25\ \text{km}^2$ | Locality spatial footprint. |
| `population_density` | Float | $4,800 - 62,000\ /\text{km}^2$ | Resident density per square kilometer. |
| `uhi_index` | Float | $0.40 - 0.95$ | Urban Heat Island Index (proxy for built-up density, thermal mass, and lack of canopy). |
| `uhi_category` | String | High, Medium, Low | Categorical binning of built-up thermal density. |
| `police_chowkis` | Integer | $1 - 7$ | Operational police outposts / chowkis within the locality boundaries. |
| `police_density` | Float | $0.8 - 14.0\ /\text{km}^2$ | Police outposts per square kilometer. |
| `internet_pct` | Float | $82\% - 96\%$ | Estimated digital connectivity percentage. |
| `total_crimes` | Integer | $30 - 170$ | Total recorded criminal infractions in annual window. |
| `crimes_against_women`| Integer | $3 - 22$ | Recorded FIRs involving offenses against women (harassment, stalking, assault). |
| `chowki_deficit_ratio` | Float | $1,200 - 45,000$ | Operational strain ratio: $\frac{\text{population\_density}}{\text{police\_density} + 0.1}$. |
| `risk_index` | Float | $2.5 - 26.5$ | Deterministic multi-criteria safety vulnerability index (0–30 scale). |
| `risk_tier` | String | High, Medium, Low | Operational triage tier: **High** ($\ge 15$), **Medium** ($7 - 14.9$), **Low** ($< 7$). |
| `baseline_pred` | Float | $2.0 - 25.0$ | Scaled prediction from the Naive Per-Capita Crime Baseline ($\text{crimes}/\text{pop} \times 10,000$). |
| `formula_pred` | Float | $2.5 - 26.5$ | Exact analytical value computed from the decomposed formula. |
| `ci_lower`, `ci_upper` | Float | $1.8 - 27.2$ | Analytical 95% Confidence Interval error bounds ($\pm 0.70$ margin of error). |

---

## 4. Missing Value, Duplication & Outlier Audit

- **Missing Values:** Zero null or unassigned values across all 538 rows ($0.0\%$ missingness).
- **Duplicate Records:** All 538 locality records represent distinct spatial observation rows.
- **Outliers & Extreme Values:**
  - *High Population Density:* Localities in Dharavi, Kurla, and Bharat Nagar exceed $58,000\ \text{people/km}^2$. These reflect authentic high-density informal and transit corridors in Mumbai.
  - *Chowki Deficit:* Localities like Saki Naka have over $55,000\ \text{people/km}^2$ with high incident loads, producing significant outpost strain that justifies municipal prioritization.

---

## 5. Potential Biases, Exclusions & Limitations

1. **FIR Reporting Friction Bias:** Official crime statistics represent *recorded* FIRs. Localities with lower digital connectivity ($<87\%$) and higher informal settlement density historically face acute reporting friction. CityPulse counteracts raw complaint bias by incorporating structural infrastructure deficits into its priority formula.
2. **Exclusion of Cyber / Payment Safety Data:** Payment fraud and cyber crime datasets were explicitly excluded from this physical street-safety prioritization system, as digital transaction fraud requires distinct institutional countermeasures (cyber cells, banking freeze protocols) unrelated to municipal street lighting or police beat scheduling.
3. **Non-Causal Interpretation:** Associations between environmental indicators (such as UHI index) and crime rates reflect spatial correlates (e.g., lack of open space, narrow unlit alleys, informal built-up corridors), not direct thermal causation.
4. **Planning Prototype Status:** The system is an analytical decision-support prototype. It does not replace real-time police emergency dispatch (100/112).
