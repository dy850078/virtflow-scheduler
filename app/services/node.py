import asyncio
import time
import httpx
from app.core.config import logger
from app.models.schemas import BareMetalNode


_nodes_cache = []
_cache_lock = asyncio.Lock()

# Simulate a cache for BareMetalNode  
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
async def cache_updater():
    global _nodes_cache
    while True:
        nodes = await fetch_bare_metal_nodes()
        async with _cache_lock:
            _nodes_cache = nodes
            logger.info(f"[Cache Updated] {time.strftime('%Y-%m-%d, %H:%M:%S')}: {_nodes_cache}")
        await asyncio.sleep(10)

# Get nodes from the cache
async def get_nodes():
    async with _cache_lock:
        return list(_nodes_cache)