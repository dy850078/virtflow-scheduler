import aio_pika
import asyncio
import json
import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")

async def handle_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body)
            task_id = payload.get("task_id", "UNKNOWN")
            node = payload.get("node", "NO_NODE")

            print(f"🚀 接收到任務: {task_id}, 要處理 node: {node}")
            await asyncio.sleep(2)
            print(f"✅ 任務完成: {task_id}")

        except Exception as e:
            print(f"❌ 任務失敗: {e}")

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=2)

    queue = await channel.declare_queue("task.schedule", durable=True)
    await queue.consume(handle_message, no_ack=False)

    print("🟢 Worker 已啟動，等待任務中...")

    # 👇 保持不退出
    await asyncio.Future()  # 不會完成，保持一直跑

if __name__ == "__main__":
    asyncio.run(main())