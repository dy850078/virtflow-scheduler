import asyncio
import random
from fastapi import HTTPException
from contextlib import asynccontextmanager
from app.models.schemas import SchedulingRequest
from app.services.node import get_nodes, cache_updater
from app.services.algorithm import select_best_node
from app.core.config import logger

schedule_queue = asyncio.Queue()
task_status = {}

@asynccontextmanager
async def lifespan(app):
    cache_task = asyncio.create_task(cache_updater())
    scheduler_task = asyncio.create_task(scheduler_worker())
    yield
    cache_task.cancel()
    scheduler_task.cancel()

async def scheduler_worker():
    while True:
        task_id, request, retry_count = await schedule_queue.get()
        try:
            await process_schedule_request(task_id, request, retry_count)
        except Exception as e:
            logger.error(f"[Worker] Task {task_id} failed: {e}")
        finally:
            schedule_queue.task_done()

async def process_schedule_request(task_id: str, request: SchedulingRequest, retry_count: int):
    task_status[task_id] = {"status": "processing"}
    nodes = await get_nodes()

    if not nodes:
        task_status[task_id]["status"] = "failed"
        raise HTTPException(status_code=500, detail="No available nodes in cache")

    best_node = select_best_node(request, nodes)
    if best_node:
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["result"] = best_node.model_dump()
        return

    if retry_count < 3:
        delay = 3 * retry_count + random.uniform(0, 1)
        logger.warning(f"[Retry {retry_count}] Task {task_id} failed. Retrying in {delay}s...")
        await asyncio.sleep(delay)
        await schedule_queue.put((task_id, request, retry_count + 1))
    else:
        task_status[task_id]["status"] = "failed"
        raise HTTPException(status_code=404, detail=f"Task {task_id} failed after {retry_count} retries.")