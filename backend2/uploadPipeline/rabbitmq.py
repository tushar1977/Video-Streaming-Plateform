import pika
import json
import logging

logger = logging.getLogger(__name__)


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
            f"RabbitMQ queues configured: {self.queue_name}, {self.dead_letter_queue}"
        )

    def push_status_updates(self, status_message):
        self.channel.basic_publish(
            exchange="", routing_key=self.status_queue, body=json.dumps(status_message)
        )
        logger.info("[SENT] Sent to Status queue")

    def close(self):
        if self.channel and self.channel.is_open:
            self.channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
