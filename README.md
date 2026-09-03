# RentRelief — Rental Affordability Stress Mapper

Privacy-conscious, local-first neighborhood housing-cost pressure screening using rent, utilities, commute cost, income trends, and historical records.

## Features
- Explainable 0–100 rental affordability stress score
- Low / Moderate / High / Critical classification
- Neighborhood affordability atlas
- Rent, utilities and commute burden analysis
- Income trend and rent-growth analysis
- Neighborhood deep dive
- Historical cost trends
- Scenario Lab
- Data-quality checks
- CSV report export
- Local SVG visual asset
- No external APIs

## Run locally

```bash
cd ~/Downloads/RentalAffordabilityStressMapper_Local
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 validate_project.py
python3 -m pytest -q
python3 run.py
```

The launcher finds a free local Streamlit port between 8501 and 8599.
