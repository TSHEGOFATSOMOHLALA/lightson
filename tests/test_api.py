import os

# Use an isolated in-memory-like DB for tests before the app is imported
os.environ["DATABASE_URL"] = "sqlite:///./test_outages.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


client = TestClient(app)


def _report(**overrides):
    body = {
        "outage_type": "power",
        "area": "Universitas, Bloemfontein",
        "description": "No electricity since 08:00",
    }
    body.update(overrides)
    return client.post("/outages", json=body)


def test_home_page_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "LightsON" in r.text
    assert client.get("/static/app.js").status_code == 200


def test_robots_and_sitemap():
    assert "Sitemap:" in client.get("/robots.txt").text
    assert "<urlset" in client.get("/sitemap.xml").text


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_outage():
    r = _report()
    assert r.status_code == 201
    data = r.json()
    assert data["confirmations"] == 1
    assert data["resolved"] is False


def test_duplicate_report_is_confirmed_not_duplicated():
    _report()
    r = _report(area="universitas, bloemfontein")
    assert r.json()["confirmations"] == 2
    assert len(client.get("/outages").json()) == 1


def test_timestamps_are_utc_aware():
    created = _report().json()["created_at"]
    assert created.endswith("Z") or created.endswith("+00:00")


def test_invalid_type_rejected():
    assert _report(outage_type="gas").status_code == 422


def test_filter_by_type_and_area():
    _report()
    _report(outage_type="water", area="Heidedal")
    assert len(client.get("/outages", params={"outage_type": "water"}).json()) == 1
    assert len(client.get("/outages", params={"area": "universitas"}).json()) == 1


def test_confirm_and_resolve_flow():
    oid = _report().json()["id"]
    assert client.post(f"/outages/{oid}/confirm").json()["confirmations"] == 2

    resolved = client.post(f"/outages/{oid}/resolve").json()
    assert resolved["resolved"] is True
    assert resolved["resolved_at"] is not None

    assert client.post(f"/outages/{oid}/confirm").status_code == 409
    assert client.get("/outages").json() == []
    assert len(client.get("/outages", params={"active_only": False}).json()) == 1


def test_not_found():
    assert client.post("/outages/999/confirm").status_code == 404


def test_area_summary_ranking():
    _report()
    _report(outage_type="water")
    _report(outage_type="internet", area="Heidedal")
    summary = client.get("/areas").json()
    assert summary[0]["area"] == "Universitas, Bloemfontein"
    assert summary[0]["active_reports"] == 2
