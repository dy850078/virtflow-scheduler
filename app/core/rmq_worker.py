import aio_pika
import asyncio
import json
import os
from task_db import update_task_status

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")


async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body)
            task_id = payload.get("task_id", "UNKNOWN")
            requested_pool = payload.get("requested_pool", "NO_POOL")

            update_task_status(task_id, "running")

            print(f"[Worker] Task Received: {task_id}, Request Pool: {requested_pool}")
            await asyncio.sleep(10)

            update_task_status(task_id, "success")
            print(f"[Worker] Task Success: {task_id}")

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