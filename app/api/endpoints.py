from fastapi import APIRouter, HTTPException
from app.models.schemas import BareMetalNode, SchedulingRequest
from app.services import scheduler
from app.core import worker

router = APIRouter()

@router.post("/schedule")
async def schedule_vm(request: SchedulingRequest):
    task_id = await scheduler.submit_task(request)
    return {"task_id": task_id, "message": "Task submitted, check status later."}

@router.get("/schedule/{task_id}")
async def check_status(task_id: str):
    status = worker.task_status.get(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return status