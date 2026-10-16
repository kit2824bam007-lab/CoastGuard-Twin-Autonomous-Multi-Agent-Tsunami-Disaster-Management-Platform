"""
Simple in-memory WebSocket connection manager for broadcasting real-time
alerts to every connected dashboard client.

For multi-instance/horizontal scaling in production, back this with Redis
Pub/Sub (redis-py asyncio) instead of an in-process list — see README
"Scaling considerations".
"""
import json
import logging
import asyncio
try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None
from fastapi import WebSocket
from app.config import settings

logger = logging.getLogger("tsunami.ws")


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.redis_client = None
        self.pubsub = None
        self.redis_task = None
        redis_host = getattr(settings, "redis_host", "localhost")
        redis_port = getattr(settings, "redis_port", 6379)
        self.redis_url = getattr(settings, "redis_url", None) or f"redis://{redis_host}:{redis_port}/0"

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WS client connected. Total: {len(self.active_connections)}")
        if self.redis_task is None:
            self.redis_task = asyncio.create_task(self._listen_redis())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WS client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, payload: dict):
        message = json.dumps(payload, default=str)
        if aioredis is None:
            await self._local_broadcast(message)
            return
        try:
            if self.redis_client is None:
                self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.publish("tsunami_alerts", message)
            logger.info("Published alert payload to Redis channel 'tsunami_alerts'")
        except Exception as e:
            logger.warning(f"Redis publish failed ({e}). Falling back to local broadcast.")
            await self._local_broadcast(message)

    async def _local_broadcast(self, message: str):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    async def _listen_redis(self):
        if aioredis is None:
            logger.info("aioredis module not present; using in-memory WebSocket broadcast.")
            return
        logger.info(f"Initializing Redis Pub/Sub alert pipeline listener on {self.redis_url}")
        while True:
            try:
                if self.redis_client is None:
                    self.redis_client = aioredis.from_url(self.redis_url, decode_responses=True)
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe("tsunami_alerts")
                
                async for msg in self.pubsub.listen():
                    if msg["type"] == "message":
                        await self._local_broadcast(msg["data"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Redis Pub/Sub connection lost/failed ({e}). Retrying in 30 seconds...")
                await asyncio.sleep(30)


manager = ConnectionManager()
