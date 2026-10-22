# Mumbai Women Safety Risk Map

Streamlit app showing locality-wise women-safety risk for Mumbai.
Locations, place search and police stations come from **OpenStreetMap** (Nominatim + Overpass) – no API keys.

## Files
| File | Purpose |
|---|---|
| `streamlit_app.py` | the app (main file for Streamlit Cloud) |
| `osm_utils.py` | OpenStreetMap helpers |
| `geocode_localities.py` | one-time script that builds `locality_coords.csv` |
| `mumbai_women_safety.csv` | dataset |
| `locality_coords.csv` | (recommended) pre-computed OSM coordinates |
| `requirements.txt` | dependencies |

## Run locally
```bash
pip install -r requirements.txt
python geocode_localities.py      # one time, ~10-15 min, creates locality_coords.csv
streamlit run streamlit_app.py
```

## Deploy
1. Push all files to a GitHub repo (include `locality_coords.csv`).
2. share.streamlit.io → New app → pick repo, branch, main file `streamlit_app.py`.
