import time
import asyncio
import logging
from sqlalchemy.orm import Session
from models import DerivAccount
from config import Config

logger = logging.getLogger("deriv_service")

class DerivMonitor:
    def __init__(self):
        self.last_check_time = 0
        self.cached_status = {
            "status": "operational",
            "latency_ms": 42.5,
            "connected_accounts": 0,
            "demo_accounts": 0,
            "real_accounts": 0,
            "ws_endpoint": Config.DERIV_WS_URL,
            "app_id": Config.DERIV_APP_ID,
            "last_ping": "Just now"
        }

    async def ping_deriv_api(self):
        """ Simulates/measures WebSocket connectivity to Deriv API server """
        start_time = time.time()
        try:
            # Short connection test check (mocked/safe network check)
            await asyncio.sleep(0.05) # Simulated light network ping
            latency = round((time.time() - start_time) * 1000, 2)
            self.cached_status["latency_ms"] = latency
            self.cached_status["status"] = "operational"
        except Exception as e:
            logger.error(f"Deriv API ping failed: {e}")
            self.cached_status["status"] = "degraded"
            self.cached_status["latency_ms"] = 999.0
        
        self.last_check_time = time.time()
        return self.cached_status

    def get_deriv_metrics(self, db: Session):
        """ Returns non-sensitive aggregate account metrics """
        try:
            total_accounts = db.query(DerivAccount).count()
            demo_accounts = db.query(DerivAccount).filter(DerivAccount.account_type == "demo").count()
            real_accounts = db.query(DerivAccount).filter(DerivAccount.account_type == "real").count()
            
            self.cached_status["connected_accounts"] = total_accounts
            self.cached_status["demo_accounts"] = demo_accounts
            self.cached_status["real_accounts"] = real_accounts
        except Exception as e:
            logger.error(f"Failed to query Deriv metrics from DB: {e}")
        
        return self.cached_status

deriv_monitor = DerivMonitor()
