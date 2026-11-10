# 💡 LightsON

A small REST API that lets people in a community report and track **power, water, internet and mobile-data outages**, so neighbours can see what is affected and stop duplicating the same report.

Built with **FastAPI**, **SQLAlchemy 2** and **pytest**. Uses SQLite locally and works with PostgreSQL via `DATABASE_URL`.

## Why it exists

Load-shedding, water cuts and patchy connectivity affect daily life, but information is scattered across WhatsApp groups. This API gives a single place to report and check what is down in your area.

## Features

- Report an outage (`power`, `water`, `internet`, `mobile_data`) for an area
- Duplicate reports of the same type in the same area are merged and counted as **confirmations**
- Confirm and resolve outages
- Filter by type and area; see which areas have the most active problems
- Input validation, automatic OpenAPI docs, test suite

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 for the web app and http://127.0.0.1:8000/docs for the interactive API docs.

## Run tests

```bash
pytest -q
```

## API overview

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/outages` | Report an outage (merges with an existing active report) |
| GET | `/outages` | List outages (`outage_type`, `area`, `active_only`, `limit`) |
| POST | `/outages/{id}/confirm` | "I'm affected too" |
| POST | `/outages/{id}/resolve` | Mark as resolved |
| GET | `/areas` | Areas ranked by active reports |

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./outages.db` | Use a PostgreSQL URL in production (add `psycopg2-binary`) |

## Roadmap

- [x] Simple web frontend (report form, live feed, filters)
- [ ] Map view
- [ ] Notifications for subscribed areas
- [ ] Network self-check tool ("is it my router or my ISP?")
- [ ] Docker + deployment
- [ ] Rate limiting and basic abuse protection

## Author

Tshegofatso Mohlala
