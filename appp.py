import os
import logging
import datetime
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import socketio
from starlette.middleware.sessions import SessionMiddleware

from config import Config
from database import engine, Base, SessionLocal
from models import AdminUser, FeatureFlag, SystemConfig, SupportTicket, DerivAccount, InjustifyUser
from middleware.auth_rbac import hash_password
from middleware.security import SecurityHeadersMiddleware
from routes.admin_api import admin_router

from routes.main import main_router
from routes.profile import profile_router
from routes.downloads import router as downloads_router
from routes.notifications import notifications_router
from routes.globalp import global_router
from routes.history import history_router
from routes.songs import router as songs_router
from routes.stream import router as stream_router
from routes.download_streams import router as d_streams_router
from web_app import app, INJUserNamespace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("appp")

# Create static media directories
media_directory = "static"
os.makedirs(os.path.join(media_directory, "admin"), exist_ok=True)
os.makedirs(os.path.join(media_directory, "songs"), exist_ok=True)
os.makedirs(os.path.join(media_directory, "thumbnails"), exist_ok=True)
os.makedirs(os.path.join(media_directory, "uploads"), exist_ok=True)

# Register Security Headers and Sessions
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ALLOWED_ORIGINS, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO Setup
sio_server = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*", 
    logger=False,
    engineio_logger=False
)
sio_app = socketio.ASGIApp(sio_server)

app.mount("/ws", sio_app)
sio_server.register_namespace(INJUserNamespace("/inj-user"))

app.mount("/static", StaticFiles(directory=media_directory), name="static")

# Include Core Routers
app.include_router(main_router, prefix="")
app.include_router(profile_router, prefix="/api/profile")
app.include_router(downloads_router, prefix="/api")
app.include_router(notifications_router, prefix="/api/notifications")
app.include_router(global_router, prefix="/global")
app.include_router(history_router, prefix="/api/history")
app.include_router(songs_router, prefix="/api/songs")
app.include_router(stream_router, prefix="/api/stream")
app.include_router(d_streams_router, prefix="/api/download_streams")

# Include Modernized Admin Router
app.include_router(admin_router)

# Serve Modern Web Administration Interface
@app.get("/admin-ui")
@app.get("/admin")
async def serve_admin_ui():
    admin_index = os.path.join(Config.BASE_DIR, "static", "admin", "index.html")
    if os.path.exists(admin_index):
        return FileResponse(admin_index)
    return RedirectResponse(url="/docs")

# Startup Data Seeding & Database Schema Initialization
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing Enterprise Backend Architecture & Database Schema...")
    try:
        Base.metadata.create_all(bind=engine)
        
        # Seed default Admin User if none exists
        db = SessionLocal()
        try:
            admin_count = db.query(AdminUser).count()
            if admin_count == 0:
                default_admin = AdminUser(
                    username="admin",
                    email="admin@injustify.com",
                    password_hash=hash_password("AdminPass123!"),
                    role="superadmin",
                    is_superadmin=True,
                    status="active"
                )
                db.add(default_admin)
                db.commit()
                logger.info("Seeded default SuperAdmin account: 'admin' / 'AdminPass123!'")

            # Seed Feature Flags
            flags = [
                ("maintenance_mode", False, "Platform-wide maintenance state"),
                ("deriv_integration", True, "Deriv API WebSocket trading bridge"),
                ("high_quality_streaming", True, "High-fidelity audio playback"),
                ("audit_logging", True, "Enterprise compliance audit logs")
            ]
            for fname, enabled, desc in flags:
                existing = db.query(FeatureFlag).filter(FeatureFlag.flag_name == fname).first()
                if not existing:
                    db.add(FeatureFlag(flag_name=fname, is_enabled=enabled, description=desc))
            db.commit()

            # Seed demo user & deriv account if empty
            if db.query(InjustifyUser).count() == 0:
                demo_u = InjustifyUser(
                    id="u_demo_101",
                    name="Enterprise Trader",
                    email="trader@injustify.com",
                    status="active",
                    role="user"
                )
                db.add(demo_u)
                db.commit()

                d_acc = DerivAccount(
                    user_id="u_demo_101",
                    account_id="CR908123",
                    currency="USD",
                    balance=12450.00,
                    account_type="real",
                    status="connected"
                )
                db.add(d_acc)
                db.commit()

        finally:
            db.close()

    except Exception as err:
        logger.error(f"Startup initialization error: {err}")

@app.on_event("shutdown")
async def on_shutdown():
    await Config.close_db_pool()

if __name__ == "__main__":
    uvicorn.run("appp:app", host="127.0.0.1", port=5000, reload=True, log_level="info")