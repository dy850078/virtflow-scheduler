import asyncio
import time
import httpx
from pydantic import ValidationError
from app.core.config import logger
from app.models.schemas import BareMetalNode


_nodes_cache = []
_cache_lock = asyncio.Lock()

# Simulate a cache for BareMetalNode  
async def fetch_bare_metal_nodes():
    print("🐛 [DEBUG] fetch_bare_metal_nodes() CALLED")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:5000/nodes", timeout=5)
            response.raise_for_status()

            raw_data = response.json()
            print(f"📦 [DEBUG] response.json() → {type(raw_data)} → {raw_data}")
            logger.info(f"[Raw Data Type] {type(raw_data)}")
            logger.info(f"[Raw Response] {raw_data}")

            if not isinstance(raw_data, list):
                print("❌ [ERROR] response.json() is not a list!")
                return []

            valid_nodes = []
            for i, node in enumerate(raw_data):
                print(f"🔍 [DEBUG] node[{i}] = {node}")
                try:
                    model = BareMetalNode(**node)
                    valid_nodes.append(model)
                    print(f"✅ [Parsed] {model.name}")
                except ValidationError as ve:
                    print(f"❌ [Validation Error @node {i}] {ve}")
                    logger.error(f"[Validation Error @node {i}] {ve}")
            return valid_nodes

        except Exception as e:
            print(f"❌ [Fetch Exception] {e}")
            logger.error(f"[Fetch Exception] {e}")
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