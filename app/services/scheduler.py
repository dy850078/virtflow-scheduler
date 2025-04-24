import uuid
from app.models.schemas import SchedulingRequest, BareMetalNode
from app.core.worker import schedule_queue, task_status
from typing import List, Optional
from app.services.algorithm import select_best_node



# Schedule a task to find the best node
async def submit_task(request: SchedulingRequest):
    task_id = str(uuid.uuid4())
    task_status[task_id] = {"status": "pending", "result": None}
    await schedule_queue.put((task_id, request, 0))
    return task_id

def run_scheduler(nodes: List[BareMetalNode], request: SchedulingRequest) -> Optional[str]:
    selected = select_best_node(request, nodes)
    return selected.name if selected else None