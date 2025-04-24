import aio_pika
import asyncio
import json
import os
from app.models.schemas import SchedulingRequest
from app.core.task_db import update_task_status
from app.services.node import get_nodes, fetch_bare_metal_nodes
from app.services.scheduler import run_scheduler
from app.core.config import logger


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body)
            task_id = payload.get("task_id", "UNKNOWN")
            requested_pool = payload.get("requested_pool", "NO_POOL")

            update_task_status(task_id, "running")

            print(f"[Worker] Task Received: {task_id}, Request Pool: {requested_pool}")
            # await asyncio.sleep(10)

            request = SchedulingRequest(**payload)
            nodes = await fetch_bare_metal_nodes()
            logger.info(f"[Available] {[nodes]}")
            selected_node = run_scheduler(nodes, request)
            
            if selected_node:
                update_task_status(task_id, "success", error=None, selected_node=selected_node)
                print(f"[Worker] Task {task_id} Success, selected node: {selected_node}")
            else:
                update_task_status(task_id, "failed", error="No suitable node found")
                print(f"[Worker] Task {task_id} Failed, selected node: {selected_node}")

        except Exception as e:
            print(f"[Worker] Task Failed: {e}")
            update_task_status(task_id, "failed")


async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=2)

    queue = await channel.declare_queue("task.schedule", durable=True)
    await queue.consume(handle_message, no_ack=False)

    print("[Worker] Worker Activated, Waiting for task...")

    # Keep processing
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())