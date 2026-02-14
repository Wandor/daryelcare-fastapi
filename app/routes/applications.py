"""REST endpoints for application CRUD and timeline events."""

import re

from fastapi import APIRouter, HTTPException
from app.database import get_pool
from app.services import application_service as svc

router = APIRouter(prefix="/api/applications")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

VALID_STAGES = frozenset([
    "new", "form-submitted", "checks", "review",
    "approved", "blocked", "registered",
])

VALID_TIMELINE_TYPES = frozenset(["action", "complete", "alert", "note"])

MAX_FIRST_NAME = 200
MAX_LAST_NAME = 200
MAX_EMAIL = 254
MAX_EVENT_LENGTH = 2000


@router.get("/")
async def list_applications():
    pool = get_pool()
    return await svc.get_all_applications(pool)


@router.get("/{app_id}")
async def get_application(app_id: str):
    pool = get_pool()
    app = await svc.get_application(pool, app_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.post("/", status_code=201)
async def create_application(body: dict):
    personal = body.get("personal") or {}

    first_name = (personal.get("firstName") or "").strip()
    last_name = (personal.get("lastName") or "").strip()
    email = (personal.get("email") or "").strip()

    if not first_name or not last_name or not email:
        raise HTTPException(
            status_code=400,
            detail="First name, last name, and email are required",
        )

    if len(first_name) > MAX_FIRST_NAME:
        raise HTTPException(
            status_code=400,
            detail=f"First name must not exceed {MAX_FIRST_NAME} characters",
        )

    if len(last_name) > MAX_LAST_NAME:
        raise HTTPException(
            status_code=400,
            detail=f"Last name must not exceed {MAX_LAST_NAME} characters",
        )

    if len(email) > MAX_EMAIL:
        raise HTTPException(
            status_code=400,
            detail=f"Email must not exceed {MAX_EMAIL} characters",
        )

    if not EMAIL_REGEX.match(email):
        raise HTTPException(
            status_code=400,
            detail="Invalid email format",
        )

    personal["firstName"] = first_name
    personal["lastName"] = last_name
    personal["email"] = email
    body["personal"] = personal

    pool = get_pool()
    app_id = await svc.create_application(pool, body)
    return {"id": app_id, "message": "Application submitted successfully"}


@router.patch("/{app_id}")
async def update_application(app_id: str, body: dict):
    stage = body.get("stage")
    if stage is not None and stage not in VALID_STAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Must be one of: {', '.join(sorted(VALID_STAGES))}",
        )

    pool = get_pool()
    updated = await svc.update_application(pool, app_id, body)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Application not found or no valid fields",
        )
    return {"message": "Application updated"}


@router.delete("/{app_id}")
async def delete_application(app_id: str):
    pool = get_pool()
    deleted = await svc.delete_application(pool, app_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application deleted"}


@router.post("/{app_id}/timeline", status_code=201)
async def add_timeline_event(app_id: str, body: dict):
    event = body.get("event")
    if not event:
        raise HTTPException(status_code=400, detail="Event text is required")

    if len(event) > MAX_EVENT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Event text must not exceed {MAX_EVENT_LENGTH} characters",
        )

    event_type = body.get("type", "action")
    if event_type not in VALID_TIMELINE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type. Must be one of: {', '.join(sorted(VALID_TIMELINE_TYPES))}",
        )

    pool = get_pool()
    entry = await svc.add_timeline_event(pool, app_id, event, event_type)
    return entry
