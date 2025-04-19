import uuid
from app.models.schemas import SchedulingRequest
from app.core.worker import schedule_queue, task_status




# Schedule a task to find the best node
async def submit_task(request: SchedulingRequest):
    task_id = str(uuid.uuid4())
    task_status[task_id] = {"status": "pending", "result": None}
    await schedule_queue.put((task_id, request, 0))
    return task_id