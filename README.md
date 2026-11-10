# 💡 LightsON

**Is it just you, or the whole street?** A community web app where people report and check power, water, Wi-Fi/fibre and mobile data outages in their area.

### 🔗 [Live demo: lightson.onrender.com](https://lightson.onrender.com/)

> The demo runs on a free plan, so the first load can take about 30 seconds.

## Why I built it

Load-shedding, water cuts and patchy connectivity affect daily life, but updates are scattered across WhatsApp groups. LightsON gives neighbours one place to report a problem, confirm it, and see when it's fixed.

## Features

- Report an outage by type and area
- Duplicate reports in the same area are merged and counted
- "I'm affected too" and "It's back" buttons
- Filter by type and search by area
- Works on mobile

## Built with

Python, FastAPI, SQLAlchemy, PostgreSQL, pytest, HTML/CSS/JavaScript. Hosted on Render.

## Run locally

```bash
git clone https://github.com/TSHEGOFATSOMOHLALA/lightson.git
cd lightson
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `127.0.0.1:8000` in your browser (API docs at `127.0.0.1:8000/docs`).

Run the tests with `pytest -q`.

## Roadmap

- [ ] Map view
- [ ] Notifications for subscribed areas
- [ ] Rate limiting and abuse protection

## Author

Tshegofatso Mohlala · tshegofatsomohlala99@gmail.com
