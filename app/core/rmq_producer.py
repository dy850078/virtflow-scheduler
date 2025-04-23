import aio_pika
import asyncio
import json
import uuid
import os

# RabbitMQ 的連線字串
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

# 發送任務的主函式
async def publish_task(payload: dict) -> str:
    # 建立與 RabbitMQ 的非同步連線
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        # 開一個頻道（channel 是 AMQP 的基礎通訊管道）
        channel = await connection.channel()
        
        # 宣告任務佇列（如果佇列已存在就不會重建）
        queue_name = "task.schedule"
        await channel.declare_queue(queue_name, durable=True)

        # 產生一個唯一的任務 ID（UUID）
        message_id = str(uuid.uuid4())
        payload["task_id"] = message_id  # 加入任務 ID

        # 建立一個 RabbitMQ 訊息
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,  # 讓訊息在 broker crash 後仍保留
            message_id=message_id
        )

        # 將訊息送出到預設的 exchange，routing_key 指向 queue
        await channel.default_exchange.publish(message, routing_key=queue_name)

        print(f"[Success] Task sent: {message_id}")
        return message_id