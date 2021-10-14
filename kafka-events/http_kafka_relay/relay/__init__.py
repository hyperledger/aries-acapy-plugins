"""HTTP to Kafka Relay."""
import logging
import os
import json
import base64

from aiokafka import AIOKafkaProducer
from fastapi import Depends, FastAPI, Request, Response

DEFAULT_BOOTSTRAP_SERVER = "kafka"
DEFAULT_INBOUND_TOPIC = "acapy-inbound-message"
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", DEFAULT_BOOTSTRAP_SERVER)
INBOUND_TOPIC = os.environ.get("INBOUND_TOPIC", DEFAULT_INBOUND_TOPIC)

app = FastAPI(title="HTTP to Kafka Relay", version="0.1.0")
LOGGER = logging.getLogger("uvicorn.error." + __name__)


class ProducerDependency:
    """Hold a single producer across requests."""

    def __init__(self):
        """Create Dependency."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP, enable_idempotence=True
        )
        self.started = False

    async def __call__(self) -> AIOKafkaProducer:
        """Retrieve producer."""
        return self.producer


producer_dep = ProducerDependency()


@app.on_event("startup")
async def start_producer():
    """Start up kafka producer on startup."""
    LOGGER.info("Starting Kafka Producer...")
    await producer_dep.producer.start()
    LOGGER.info("Kafka Producer started")


@app.on_event("shutdown")
async def stop_producer():
    """Stop producer on shutdown."""
    LOGGER.info("Stopping Kafka Producer...")
    await producer_dep.producer.stop()
    LOGGER.info("Kafka Producer stopped")


@app.post("/")
async def receive_message(
    request: Request, producer: AIOKafkaProducer = Depends(producer_dep)
):
    """Receive a new agent message and post to Kafka."""
    message = await request.body()
    value = str.encode(
        json.dumps(
            {
                "payload": base64.urlsafe_b64encode(message).decode(),
            }
        ),
    )
    LOGGER.debug("Received message, pushing to Kafka: %s", value)
    await producer.send_and_wait(INBOUND_TOPIC, value)
    return Response(status_code=200)
