from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import logging
import time
from typing import List
from pydantic import BaseModel
from contextlib import asynccontextmanager


# BareMetalNode Definition
class BareMetalNode(BaseModel):
    name: str
    cpu: int
    memory: int
    storage: int
    usage_cpu: float
    usage_mem: float
    pool: str
    dedicated: bool
    model: str
    max_vms: int
    current_vms: int

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
    task = asyncio.create_task(update_nodes_cache())
    yield
    task.cancel()

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
        and node.current_vms < node.max_vms
    ]

def score_nodes (nodes: List[BareMetalNode]):
    cpu_weight = 1
    mem_weight = 1
    nodes.sort(key=lambda node: (cpu_weight * node.usage_cpu + mem_weight * node.usage_mem) / 2 + (node.current_vms / node.max_vms))
    return nodes


# Select suitable node for the request
def select_best_node(request: SchedulingRequest, nodes: List[BareMetalNode]):
    nodes = pre_filter(request, nodes)
    logger.info(f"[Pre-filtered] {[node.name for node in nodes]}")

    nodes = filter_nodes(request, nodes)
    logger.info(f"[Filtered] {[node.name for node in nodes]}")

    candidates = score_nodes(nodes)
    logger.info(f"[Scored] {[candidate.name for candidate in candidates]}")
    logger.info(f"[Selected] {candidates[0].name if candidates else None}")

    return candidates[0] if candidates else None

# Scheduler API
@app.post("/schedule")
async def schedule(request: SchedulingRequest):
    nodes = await get_nodes()
    best_node = select_best_node(request, nodes)
    if not best_node:
        raise HTTPException(status_code=404, detail="No suitable node found")
    return {"node": best_node}
