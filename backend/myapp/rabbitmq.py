import pika
import logging
import json
import time
import uuid
from typing import Dict, Any
from datetime import datetime
from . import sock

logger = logging.getLogger("myapp.RabbitMQ")


def createChannel():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            "localhost",
            heartbeat=600,
            blocked_connection_timeout=300,
        )
    )

    channel = connection.channel()
    return channel


class VideoQueueManager:
    def __init__(self) -> None:
        self.channel = createChannel()
        self.queue_name = "upload"
        self.dead_letter_queue = "upload_failed"
        self.status_queue = "status_updates"
        self._setup_queues()

    def _setup_queues(self):
        self.channel.queue_declare(
            self.queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "",
                "x-dead-letter-routing-key": self.dead_letter_queue,
            },
        )
        self.channel.queue_declare(queue=self.dead_letter_queue, durable=True)

        self.channel.queue_declare(queue=self.status_queue, durable=True)

        logger.info(
            f"RabbitMQ queues configured: {self.queue_name}, {self.dead_letter_queue}, {self.status_queue}"
        )

    def push_video(self, video_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        user_id = video_data.get("user_id")
        base_name = video_data.get("base_name")
        message = {
            "job_id": job_id,
            "data": video_data,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "attempts": 0,
                "user_id": video_data.get("user_id"),
            },
        }

        properties = pika.BasicProperties(
            delivery_mode=2,
            message_id=job_id,
            timestamp=int(time.time()),
            content_type="application/json",
        )

        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=json.dumps(message),
            properties=properties,
        )
        self._send_queued_status(user_id, base_name, job_id)

        logger.info(
            f"Video Data pushed to Queue with Job Id {job_id} \n for user {video_data.get('user_id')}"
        )
        return job_id

    def _send_queued_status(self, user_id: str, base_name: str, job_id: str):
        progress_msg = {
            "user_id": user_id,
            "base_name": base_name,
            "status": "queued",
            "progress": 0,
            "timestamp": datetime.now().isoformat(),
            "job_id": job_id,
            "message": "Waiting for available runner...",
        }

        sock.emit("send_updates", progress_msg, room=f"userId_{user_id}")
        logger.info(f"✓ Sent 'queued' status to user {user_id}")

    def get_queue_status(self):
        try:
            method = self.channel.queue_declare(
                queue=self.queue_name,
                passive=True,
            )
            pending_jobs = method.method.message_count

            return {
                "queue_name": self.queue_name,
                "pending_jobs": pending_jobs,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"✗ Failed to get queue stats: {e}")
            return {
                "queue_name": self.queue_name,
                "pending_jobs": 0,
                "error": str(e),
            }

    def get_queue_size(self) -> int:
        method = self.channel.queue_declare(queue=self.queue_name, passive=True)
        return method.method.message_count

    def close(self):
        if self.channel and self.channel.is_open:
            self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
