from fastapi import APIRouter, HTTPException
from app.core.rmq_producer import publish_task
from app.models.schemas import BareMetalNode, SchedulingRequest
from app.services import scheduler
from app.core import worker
from app.core.task_db import get_task_status

router = APIRouter()

@router.post("/schedule")
async def schedule_task(payload: SchedulingRequest):
    task_id = await publish_task(payload.dict())
    return {"task_id": task_id, "status": "queued"}

@router.get("/status/{task_id}")
async def check_status(task_id: str):
    return get_task_status(task_id)