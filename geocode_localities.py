"""
ONE-TIME helper: look up every locality in the CSV on OpenStreetMap (Nominatim)
and save the result to  locality_coords.csv.

    python geocode_localities.py

Takes ~10-15 minutes for 538 rows (Nominatim allows 1 request/second).
Safe to stop and re-run: it resumes where it left off.
Commit locality_coords.csv to GitHub so the deployed app starts instantly.
"""
import os
import pandas as pd
from osm_utils import geocode_locality

CSV = "mumbai_women_safety.csv"
OUT = "locality_coords.csv"

df = pd.read_csv(CSV)
done = pd.read_csv(OUT) if os.path.exists(OUT) else pd.DataFrame(
    columns=["row_id", "locality", "lat", "lon", "status"])
done_ids = set(done["row_id"].astype(int))
rows = done.to_dict("records")
anchor = None

for i, name in enumerate(df["locality"].astype(str), start=1):
    prev = next((r for r in rows if r["row_id"] == i), None)
    if prev:
        if prev["status"] == "ok":
            anchor = (prev["lat"], prev["lon"])
        continue
    status, lat, lon = geocode_locality(name, anchor)
    if status == "error":
        print(f"[{i}/{len(df)}] {name}: network error, stopping. Re-run later.")
        break
    if status == "ok":
        anchor = (lat, lon)
    rows.append({"row_id": i, "locality": name, "lat": lat, "lon": lon, "status": status})
    print(f"[{i}/{len(df)}] {name}: {status} {lat} {lon}")
    if i % 20 == 0:
        pd.DataFrame(rows).to_csv(OUT, index=False)

pd.DataFrame(rows).to_csv(OUT, index=False)
ok = sum(r["status"] == "ok" for r in rows)
print(f"\nSaved {OUT}: {ok}/{len(df)} localities located.")
