import os
import pymysql
import asyncio
import aiomysql
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI() 

app.mount("/static", StaticFiles(directory="static"), name="static")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'injustify_super_secret_enterprise_key_2026')
    JWT_SECRET = os.getenv('JWT_SECRET', 'injustify_jwt_admin_secret_key_998877')
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = 480

    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLITE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'mydb.sqlite')}"
    
    # Priority: DB_URL env var -> MySQL -> SQLite fallback
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'mydb.sqlite')}")

    SONGS_FOLDER = os.path.join(BASE_DIR, 'static', 'songs')
    THUMBNAILS_upload_FOLDER = os.path.join('static', 'thumbnails')
    PROFILE_UPLOAD_FOLDER = os.path.join('static', 'uploads')

    CORS_ALLOWED_ORIGINS = [
        "http://example.com",
        "http://192.168.100.2:5000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:8080",
        "http://192.168.100.2:8080",
        "http://localhost:5173"
    ]

    FRONTEND_SERVER = os.getenv("FRONTEND_SERVER", "http://localhost:8080")
    BACKEND_SERVER = os.getenv("BACKEND_SERVER", "http://127.0.0.1:5000")

    thumbnailPath = f"{BACKEND_SERVER}/static/thumbnails"
    profilePath = f"{BACKEND_SERVER}/static/uploads"

    # Deriv Integration Config
    DERIV_APP_ID = os.getenv("DERIV_APP_ID", "1089")
    DERIV_WS_URL = os.getenv("DERIV_WS_URL", "wss://ws.derivws.com/websockets/v3")

    class SafeCursor:
        def execute(self, *args, **kwargs): pass
        def fetchone(self, *args, **kwargs): return None
        def fetchall(self, *args, **kwargs): return []
        def close(self): pass

    class SafeDb:
        def cursor(self, *args, **kwargs): return Config.SafeCursor()
        def commit(self): pass

    try:
        mydb = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "0000"),
            database=os.getenv("DB_NAME", "injustify")
        )
    except Exception:
        mydb = SafeDb()

    pool = None  

    db_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "0000"),
        "db": os.getenv("DB_NAME", "injustify"),
        "port": int(os.getenv("DB_PORT", "3306"))
    }

    @staticmethod
    async def init_db_pool():
        """ Initialize and store the connection pool safely. """
        if Config.pool is None:
            try:
                Config.pool = await aiomysql.create_pool(**Config.db_config)
            except Exception as err:
                logging.warning(f"aiomysql pool init skipped (using SQLite fallback): {err}")
                Config.pool = None
    
    @staticmethod
    async def get_db_connection():
        """ Get a database connection from the pool if available. """
        if Config.pool is None:
            await Config.init_db_pool()  
        
        if Config.pool:
            conn = await Config.pool.acquire() 
            return conn
        return None

    @staticmethod
    async def close_db_pool():
        """ Close the database connection pool. Should be called at shutdown. """
        if Config.pool:
            Config.pool.close()
            await Config.pool.wait_closed()

    @classmethod
    def get_sanitized_config(cls):
        """ Returns non-sensitive application settings for the Admin UI. """
        return {
            "environment": os.getenv("ENVIRONMENT", "production"),
            "backend_server": cls.BACKEND_SERVER,
            "frontend_server": cls.FRONTEND_SERVER,
            "deriv_app_id": cls.DERIV_APP_ID,
            "deriv_ws_url": cls.DERIV_WS_URL,
            "jwt_expire_minutes": cls.JWT_EXPIRE_MINUTES,
            "database_driver": "SQLite (Local)" if "sqlite" in cls.DATABASE_URL else "MySQL (Production)",
            "cors_origins": cls.CORS_ALLOWED_ORIGINS,
            "media_directories": {
                "songs": cls.SONGS_FOLDER,
                "thumbnails": cls.THUMBNAILS_upload_FOLDER,
                "uploads": cls.PROFILE_UPLOAD_FOLDER
            }
        }

