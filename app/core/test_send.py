import asyncio
from rmq_producer import publish_task

async def main():
    payload = {
        "node": "bm-node-01",
        "cpu": 8,
        "memory": 16384
    }
    await publish_task(payload)

asyncio.run(main())