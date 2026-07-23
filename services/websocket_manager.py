import time
import logging

logger = logging.getLogger("websocket_manager")

class WebSocketTracker:
    def __init__(self):
        self.active_connections = {}
        self.total_messages_received = 0
        self.total_messages_sent = 0
        self.start_time = time.time()

    def register_connection(self, sid: str, namespace: str = "/inj-user", user_id: str = None):
        self.active_connections[sid] = {
            "sid": sid,
            "namespace": namespace,
            "user_id": user_id,
            "connected_at": time.time()
        }
        logger.info(f"WS Client Connected: {sid} on {namespace}")

    def unregister_connection(self, sid: str):
        if sid in self.active_connections:
            del self.active_connections[sid]
            logger.info(f"WS Client Disconnected: {sid}")

    def record_message(self, direction: str = "inbound"):
        if direction == "inbound":
            self.total_messages_received += 1
        else:
            self.total_messages_sent += 1

    def get_stats(self):
        uptime_seconds = int(time.time() - self.start_time)
        return {
            "status": "operational",
            "active_connections": len(self.active_connections),
            "messages_received": self.total_messages_received,
            "messages_sent": self.total_messages_sent,
            "uptime_seconds": uptime_seconds,
            "namespaces": ["/inj-user", "/ws"]
        }

ws_tracker = WebSocketTracker()
