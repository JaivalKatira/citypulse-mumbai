# CityPulse Mumbai: Data Statement & Provenance Specification
**Document Version:** 1.0  
**Project:** CityPulse Mumbai — Urban Safety Vulnerability & Municipal Resource Allocation DSS  
**Challenge:** HackAMatch 1.0 — Data Science + AI Challenge  

---

## 1. Dataset Overview & Identification

- **Dataset Title:** Greater Mumbai Locality-Level Safety Risk, Infrastructure & Demographics Dataset
- **Geographic Extent:** Greater Mumbai (Island City, Western Suburbs, Eastern Suburbs)
  - Latitude: 18.89°N to 19.28°N
  - Longitude: 72.78°E to 72.98°E
- **Temporal Scope:** Consolidated annual administrative records and OpenStreetMap live infrastructure pulls (2024–2026 snapshot).
- **Unit of Observation:** Urban locality / neighborhood ($N = 538$ distinct administrative observation zones across 24 MCGM/BMC municipal wards).
- **Core Access Mode:** Publicly accessible, open data repository with zero-cost OpenStreetMap (Nominatim & Overpass API) geospatial infrastructure alignment.

---

## 2. Source Provenance & Licensing

| Component | Source Portal / Authority | License / Access Terms | Cost & Credentials |
| :--- | :--- | :--- | :--- |
| **Locality Demographics & Crimes** | Municipal Corporation of Greater Mumbai (MCGM) open datasets & NCRB administrative police ward filings. | Open Government Data / Public Research License | Free, No API key required |
| **Police Station Geometries** | OpenStreetMap (OSM) via Overpass API (`amenity=police`). | Open Database License (ODbL) © OpenStreetMap contributors | Free, No key, Rate-limit throttled |
| **Geocoding & Centroids** | OpenStreetMap Nominatim geocoding engine with ward bounding box bounds. | ODbL / OSM Foundation Acceptable Use | Free, No key, Pre-computed cache |
| **Basemap Tiles** | CartoDB Dark Matter / Positron free public raster tiles. | © OpenStreetMap contributors, © CARTO | Free public raster endpoint |

---

## 3. Data Dictionary & Schema

The curated dataset contains 538 rows and 22 curated attributes:

| Variable Name | Data Type | Units / Range | Definition & Context |
| :--- | :--- | :--- | :--- |
| `locality` | String | Categorical | Specific neighborhood name in Mumbai (e.g., Saki Naka, Bandra, Kurla, Colaba). |
| `zone` | String | Categorical | Macro-administrative zone: *Island City*, *Western Suburbs*, or *Eastern Suburbs*. |
| `ward` | String | Categorical | Brihanmumbai Municipal Corporation (BMC) administrative ward (e.g., Ward K/E, Ward L). |
| `lat`, `lon` | Float | Decimal Degrees | High-precision geographic centroid of the locality. |
| `population` | Integer | $5,600 - 32,000$ | Resident locality population based on municipal census data. |
| `area_sq_km` | Float | $0.35 - 1.25\ \text{km}^2$ | Geographic area of the locality. |
| `population_density` | Float | $4,800 - 62,000\ /\text{km}^2$ | Resident density per square kilometer. |
| `uhi_index` | Float | $0.40 - 0.95$ | Urban Heat Island Index (proxy for built-up density, thermal mass, and informal roofing). |
| `uhi_category` | String | High, Medium, Low | Categorical binning of built-up thermal density. |
| `police_chowkis` | Integer | $1 - 7$ | Count of operational police outposts / chowkis within the locality boundaries. |
| `police_density` | Float | $0.8 - 14.0\ /\text{km}^2$ | Chowkis per square kilometer. |
| `internet_pct` | Float | $82\% - 96\%$ | Estimated digital penetration and mobile connectivity in the locality. |
| `total_crimes` | Integer | $30 - 170$ | Total recorded criminal infractions in the annual reporting window. |
| `crimes_against_women`| Integer | $3 - 22$ | Recorded FIRs involving crimes against women (harassment, stalking, assault). |
| `chowki_deficit_ratio` | Float | $1,200 - 45,000$ | Engineered ratio: $\frac{\text{population\_density}}{\text{police\_density} + 0.1}$. |
| `risk_index` | Float | $2.5 - 26.5$ | Ground truth multi-criteria safety vulnerability index. |
| `risk_tier` | String | High, Medium, Low | Operational triage tier: **High** ($\ge 15$), **Medium** ($7 - 14.9$), **Low** ($< 7$). |
| `baseline_pred` | Float | $2.0 - 25.0$ | Prediction from the Naive Crime-Population Baseline Model. |
| `rf_pred` | Float | $2.5 - 26.2$ | Prediction from the Champion Random Forest Regressor. |
| `ci_lower`, `ci_upper` | Float | $0.0 - 27.5$ | 95% Confidence Interval error bounds ($\pm 1.96 \times \text{RSE}$). |

---

## 4. Missing Value, Duplication & Outlier Audit

- **Missing Values:** Zero null or unassigned values across all 538 rows ($0.0\%$ missingness).
- **Duplicate Records:** All 538 locality records are geographically or administratively distinct.
- **Outliers & Extreme Values:**
  - *High Population Density:* Localities in Dharavi, Kurla, and Bharat Nagar exceed $58,000\ \text{people/km}^2$. These were verified as authentic high-density informal and transit agglomerations rather than data entry anomalies.
  - *Chowki Deficit:* Saki Naka and Mogra Village have over $55,000\ \text{people/km}^2$ served by only 6 chowkis, generating extreme deficit ratios that drive legitimate operational vulnerability.

---

## 5. Potential Biases & Limitations (Section 13 Compliance)

1. **FIR Reporting Friction Bias:** Official crime statistics represent *recorded* first information reports. Wards with lower internet penetration and lower civic literacy historically experience reporting friction, causing raw crime numbers to under-represent real vulnerability. CityPulse explicitly balances raw crime counts with structural indicators (chowki deficits, built-up density).
2. **Fixed Administrative Centroids:** Population figures represent resident populations and do not dynamically account for floating commuter footfall (e.g., peak-hour commuter congestion at Dadar or Andheri railway junctions).
3. **Non-Causal Disclaimer:** Associations between environmental indicators (such as UHI index) and crime rates reflect spatial correlates (e.g., lack of open space, narrow unlit alleys, informal built-up corridors), not direct thermal causation.
