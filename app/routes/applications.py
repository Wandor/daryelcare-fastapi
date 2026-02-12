"""REST endpoints for application CRUD and timeline events."""

from fastapi import APIRouter, HTTPException
from app.database import get_pool
from app.services import application_service as svc

router = APIRouter(prefix="/api/applications")


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
    if not personal.get("firstName") or not personal.get("lastName") or not personal.get("email"):
        raise HTTPException(
            status_code=400,
            detail="First name, last name, and email are required",
        )
    pool = get_pool()
    app_id = await svc.create_application(pool, body)
    return {"id": app_id, "message": "Application submitted successfully"}


@router.patch("/{app_id}")
async def update_application(app_id: str, body: dict):
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
    event_type = body.get("type", "action")
    pool = get_pool()
    entry = await svc.add_timeline_event(pool, app_id, event, event_type)
    return entry
