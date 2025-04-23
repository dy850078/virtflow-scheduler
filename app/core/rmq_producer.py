import aio_pika
import asyncio
import json
import uuid
import os
from app.core.task_db import create_task


RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

async def publish_task(payload: dict) -> str:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("task.schedule", durable=True)

        message_id = str(uuid.uuid4())
        payload["task_id"] = message_id

        # Record task status in dict
        print(f"[Producer] Creating task {message_id}")
        create_task(message_id)

        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=message_id
        )

        await channel.default_exchange.publish(message, routing_key="task.schedule")
        return message_id