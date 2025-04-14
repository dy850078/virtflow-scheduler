import random
from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import logging
import time
import uuid
from typing import Dict, List
from pydantic import BaseModel
from contextlib import asynccontextmanager


schedule_queue = asyncio.Queue()
task_status: Dict[str, Dict] = {}

# BareMetalNode Definition
class BareMetalNode(BaseModel):
    name: str
    cpu: int = 0
    memory: int = 0
    storage: int = 0
    usage_cpu: float = 0.0
    usage_mem: float = 0.0
    pool: str
    dedicated: bool
    model: str
    max_vms: int = 1
    current_vms: int = 0

# SchedulingRequest Definition
class SchedulingRequest(BaseModel):
    requested_cpu: int
    requested_memory: int
    requested_pool: str
    dedicated: bool

# Simulate a cache for BareMetalNode
nodes_cache: List[BareMetalNode] = []
cache_lock = asyncio.Lock()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cache_task = asyncio.create_task(update_nodes_cache())
    schedule_task = asyncio.create_task(scheduler_worker())
    yield
    cache_task.cancel()
    schedule_task.cancel()

app = FastAPI(lifespan=lifespan)

# Fetch BareMetalNode from the mock API
async def fetch_bare_metal_nodes():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:5000/nodes", timeout=5)
            response.raise_for_status()
            return [BareMetalNode(**node) for node in response.json()]
        except httpx.HTTPError as e:
            logger.error(f"[Fetch Error] {e}")
            return []


# Update the cache every 10 seconds
async def update_nodes_cache():
    global nodes_cache
    while True:
        nodes = await fetch_bare_metal_nodes()
        async with cache_lock:
            nodes_cache = nodes
            logger.info(f"[Cache Updated] {time.strftime('%Y-%m-%d, %H:%M:%S')}: {nodes_cache}")
        await asyncio.sleep(10)


# Get nodes from the cache
async def get_nodes():
    async with cache_lock:
        return nodes_cache
    

def pre_filter(request: SchedulingRequest, nodes: List[BareMetalNode]):
    return [
        node for node in nodes
        if node.pool == request.requested_pool
        and (not request.dedicated or node.dedicated)
        and node.current_vms < node.max_vms
    ]

def filter_nodes(request: SchedulingRequest, nodes: List[BareMetalNode]):
    return [
        node for node in nodes
        if node.cpu >= request.requested_cpu
        and node.memory >= request.requested_memory
    ]

def score_nodes (nodes: List[BareMetalNode], cpu_weight=1.0, mem_weight=1.0, vm_weight=1.0):
    nodes.sort(key=lambda node: (1 - node.usage_cpu) * cpu_weight +
                                (1 - node.usage_mem) * mem_weight -
                                (node.current_vms / node.max_vms) * vm_weight)
    return nodes


# Select suitable node for the request
def select_best_node(request: SchedulingRequest, nodes: List[BareMetalNode]):
    nodes = pre_filter(request, nodes)
    # logger.info(f"[Pre-filtered] {[node.name for node in nodes]}")
    logger.info(f"[Pre-filtered] {[node for node in nodes]}") 
    nodes = filter_nodes(request, nodes)
    # logger.info(f"[Filtered] {[node.name for node in nodes]}")
    logger.info(f"[Filtered] {[node for node in nodes]}")

    candidates = score_nodes(nodes,1.0,1.0,1.0)
    logger.info(f"[Scored] {[candidate.name for candidate in candidates]}")
    logger.info(f"[Selected] {candidates[0].name if candidates else None}")

    return candidates[0] if candidates else None

async def scheduler_worker():
    while True:
        task_id, request, retry_count = await schedule_queue.get()
        try:
            result = await process_schedule_request(task_id, request, retry_count)
            logger.info(f"[Worker] Task {task_id} success: {result}")
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
        task_status[task_id]["result"] = best_node.model_dump() if best_node else None
        return {"task_id": task_id, "node": best_node}

    if retry_count < 3:
        delay = 3 * retry_count + random.uniform(0, 1)
        logger.warning(f"[Retry {retry_count}] Task {task_id} failed: {task_status[task_id]}. Retrying in {delay}s...")
        await asyncio.sleep(delay) 
        await schedule_queue.put((task_id, request, retry_count + 1))

    else:
        task_status[task_id]["status"] = "failed"
        raise HTTPException(status_code=404, detail=f"Task {task_id} failed after retring {retry_count} times.") 

# Scheduler API
@app.post("/schedule")
async def schedule(request: SchedulingRequest):
    task_id = str(uuid.uuid4())
    task_status[task_id] = {"status": "pending", "result": None}
    await schedule_queue.put((task_id, request, 0))

    return {"task_id": task_id, "message": "Task submitted, check status later."}

# Check schedule task status
@app.get("/schedule/{task_id}")
async def check_task_status(task_id: str):
    if task_id not in task_status:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return task_status[task_id]