from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db

app = FastAPI(
    title="LightsON",
    description="Report and track power, water and connectivity outages in your community.",
    version="0.1.0",
)

Base.metadata.create_all(bind=engine)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/robots.txt", include_in_schema=False)
def robots(request: Request):
    base = str(request.base_url).rstrip("/")
    return PlainTextResponse(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    base = str(request.base_url).rstrip("/")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{base}/</loc></url>\n"
        "</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/outages", response_model=schemas.OutageRead, status_code=201)
def report_outage(payload: schemas.OutageCreate, db: Session = Depends(get_db)):
    """Report an outage. If an active report of the same type exists for the
    same area, it is confirmed instead of duplicated."""
    area = payload.area.strip()
    existing = db.scalar(
        select(models.Outage).where(
            models.Outage.outage_type == payload.outage_type,
            func.lower(models.Outage.area) == area.lower(),
            models.Outage.resolved == 0,
        )
    )
    if existing:
        existing.confirmations += 1
        db.commit()
        db.refresh(existing)
        return _to_read(existing)

    outage = models.Outage(
        outage_type=payload.outage_type,
        area=area,
        description=payload.description.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(outage)
    db.commit()
    db.refresh(outage)
    return _to_read(outage)


@app.get("/outages", response_model=list[schemas.OutageRead])
def list_outages(
    outage_type: schemas.OutageType | None = None,
    area: str | None = Query(default=None, description="Case-insensitive partial match"),
    active_only: bool = True,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    stmt = select(models.Outage).order_by(models.Outage.created_at.desc()).limit(limit)
    if outage_type:
        stmt = stmt.where(models.Outage.outage_type == outage_type)
    if area:
        stmt = stmt.where(models.Outage.area.ilike(f"%{area}%"))
    if active_only:
        stmt = stmt.where(models.Outage.resolved == 0)
    return [_to_read(o) for o in db.scalars(stmt)]


@app.post("/outages/{outage_id}/confirm", response_model=schemas.OutageRead)
def confirm_outage(outage_id: int, db: Session = Depends(get_db)):
    outage = _get_or_404(db, outage_id)
    if outage.resolved:
        raise HTTPException(status_code=409, detail="Outage already resolved")
    outage.confirmations += 1
    db.commit()
    db.refresh(outage)
    return _to_read(outage)


@app.post("/outages/{outage_id}/resolve", response_model=schemas.OutageRead)
def resolve_outage(outage_id: int, db: Session = Depends(get_db)):
    outage = _get_or_404(db, outage_id)
    if not outage.resolved:
        outage.resolved = 1
        outage.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(outage)
    return _to_read(outage)


@app.get("/areas", response_model=list[schemas.AreaSummary])
def area_summary(db: Session = Depends(get_db)):
    """Areas ranked by number of active reports."""
    rows = db.execute(
        select(
            models.Outage.area,
            func.count(models.Outage.id),
            func.sum(models.Outage.confirmations),
        )
        .where(models.Outage.resolved == 0)
        .group_by(models.Outage.area)
        .order_by(func.count(models.Outage.id).desc())
    ).all()
    return [
        schemas.AreaSummary(area=a, active_reports=n, total_confirmations=int(c or 0))
        for a, n, c in rows
    ]


def _get_or_404(db: Session, outage_id: int) -> models.Outage:
    outage = db.get(models.Outage, outage_id)
    if not outage:
        raise HTTPException(status_code=404, detail="Outage not found")
    return outage


def _as_utc(value: datetime | None) -> datetime | None:
    # SQLite drops timezone info; stored values are always UTC.
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _to_read(outage: models.Outage) -> schemas.OutageRead:
    return schemas.OutageRead(
        id=outage.id,
        outage_type=outage.outage_type,
        area=outage.area,
        description=outage.description,
        latitude=outage.latitude,
        longitude=outage.longitude,
        confirmations=outage.confirmations,
        resolved=bool(outage.resolved),
        created_at=_as_utc(outage.created_at),
        resolved_at=_as_utc(outage.resolved_at),
    )
