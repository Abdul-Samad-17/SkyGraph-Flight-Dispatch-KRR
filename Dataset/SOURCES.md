# Data sources and provenance

| Data | Intended authoritative source | What is in this project |
|---|---|---|
| Airports, runways | OurAirports - https://ourairports.com/data/ (airports.csv, runways.csv) | 38 airports / 60 runways, **curated and rounded** (coordinates to 4 decimals, longest-runway figures from public aeronautical knowledge) |
| Route network | OpenFlights - https://github.com/jpatokal/openflights (routes.dat) | 153 undirected segments chosen to resemble real hub-and-spoke patterns in the study region; **not a copy of routes.dat** |
| Aircraft | OpenAP - https://github.com/junzis/openap | 6 types with rounded range, minimum runway and cruise speed |
| Airspace zones | Natural Earth - https://www.naturalearthdata.com/ | **Fictional** rectangles (RZ-ALPHA, PZ-BRAVO, RZ-CHARLIE, AZ-DELTA) |
| Weather | aviationweather.gov API, fastmeteo | **Fictional** hazard cells (STORM-1/2, TURB-3, ASH-4, ICE-5) |

## Why curated?
The environment that generated this project had no internet access, so the raw datasets could not be downloaded. Every number is plausible and internally consistent, and the whole pipeline is data-driven:
edit the CSVs (or `src/make_dataset.py`), run `python src/run_everything.py`, and every file, query result, figure and report regenerates.

## Verify before submitting (15 minutes)
1. Download `airports.csv` and `runways.csv` from OurAirports; for each of the 38 airports compare latitude, longitude and the longest runway (`length_ft x 0.3048`). Correct `Dataset/airports.csv` / `make_dataset.py` where they differ.
2. Check the 6 aircraft against OpenAP (`openap` Python package: `prop.aircraft('A388')` gives range and mass data; runway requirements are approximate field-length figures).
3. Re-run `python src/run_everything.py && python src/tests.py`. If a correction changes the data, the tests tell you which expectation changed (a few tests contain sample-specific numbers such as "18 candidates for scenario S1").

## Cleaning / transformation log
- Keep one study region; drop airports without coordinates or runway length (none dropped in the curated set).
- Validate codes: every segment endpoint exists, no self-loops, no duplicate or reversed pairs.
- Distances: haversine, R = 6371 km, rounded to 0.1 km.
- Geometry: segment x polygon intersection (lon/lat plane, closed segments, touching counts) precomputed in `src/build_kg.py`.
- Booleans, integers and decimals written as typed RDF literals.
