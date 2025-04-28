# main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import (
    Column, Integer, String, TIMESTAMP, create_engine, Enum,
    BigInteger, Text, Boolean, Date, Float
)
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import check_password_hash
from config import Config
import uvicorn
from sqlalchemy import (
    Column, String, Boolean, Time, TIMESTAMP, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
# -------------------- Database Setup --------------------
DATABASE_URL = Config.DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -------------------- Models --------------------
class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True)
    password_hash = Column(String(200))
    is_superadmin = Column(Boolean)
    
class VisitorTracking(Base):
    __tablename__ = "visitor_tracking"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    ip = Column(String(45), nullable=False)
    continent = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(100), nullable=True)
    local_time = Column(String(100), nullable=True)
    isp_org = Column(String(255), nullable=True)
    isp_name = Column(String(255), nullable=True)
    flag_emoji = Column(String(10), nullable=True)
    device = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")


class View(Base):
    __tablename__ = "views"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36))
    song_id = Column(String(10))
    view_count = Column(Integer, default=1)
    progress = Column(Float, default=0.00)
    last_viewed = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")

class Download(Base):
    __tablename__ = "downloads"
    download_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(36), nullable=False)
    song_id = Column(String(36), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_format = Column(String(50), nullable=False)
    itag = Column(String(50), nullable=False)
    downloaded_size = Column(BigInteger, nullable=False, default=0)
    file_size = Column(BigInteger, nullable=False)
    file_source = Column(String(50), nullable=False)
    download_status = Column(
        Enum("SUCCESS", "FAILED", "IN_PROGRESS"), default="IN_PROGRESS", nullable=True
    )
    user_agent = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)
    retries = Column(Integer, default=0)
    failure_reason = Column(Text, nullable=True)
    is_partial = Column(Boolean, default=False)
    thumbnail = Column(String(255), nullable=False)

class InjustifyUser(Base):
    __tablename__ = "injustifyusers"
    email = Column(String(255), nullable=False, unique=True)
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(855), nullable=True)
    verified_email = Column(Boolean, default=False)
    password = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP", nullable=True)
    status = Column(Enum("active", "inactive"), default="active", nullable=True)
    last_login = Column(TIMESTAMP, nullable=True)
    notification_setting = relationship("NotificationSetting", back_populates="user", uselist=False)


class InjustifyMusic(Base):
    __tablename__ = "injustifymusic"
    song_id = Column(String(10), primary_key=True)
    title = Column(String(255), nullable=False, index=True)
    artist = Column(String(255), nullable=False)
    album = Column(String(255), nullable=True)
    genre = Column(String(100), nullable=True)
    release_date = Column(Date, nullable=True)
    duration = Column(Float, nullable=True)
    url = Column(String(500), nullable=True)
    upload_date = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)
    is_favorite = Column(Boolean, default=False)
    views = Column(Integer, default=0)
    dislike = Column(Integer, nullable=True)
    thumbnail_path = Column(String(255), nullable=True)

class Playlist(Base):
    __tablename__ = "playlists"
    playlist_id = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)
    updated_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP", nullable=True)

class PlaylistSong(Base):
    __tablename__ = "playlistsongs"
    playlist_song_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(String(10), nullable=False)
    song_id = Column(String(10), nullable=False)
    added_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=True)

class VerificationSession(Base):
    __tablename__ = "verification_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(TIMESTAMP, nullable=False)





class NotificationSetting(Base):
    __tablename__ = "notification_settings"

    # Primary key is id, not user_id
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(String(36), ForeignKey("injustifyusers.id", ondelete="CASCADE"), nullable=False)
    user = relationship("InjustifyUser", back_populates="notification_setting", uselist=False)


    # Notification toggles
    enable_sound_alerts = Column(Boolean, default=False)
    selected_sound = Column(String(100), nullable=True)
    do_not_disturb = Column(Boolean, default=False)

    # DND Schedule
    dnd_start_time = Column(Time, nullable=True)
    dnd_end_time = Column(Time, nullable=True)

    # DND Exceptions
    dnd_allow_calls = Column(Boolean, default=False)
    dnd_allow_messages = Column(Boolean, default=False)
    dnd_allow_urgent = Column(Boolean, default=False)

    # Email Notifications
    email_newsignin = Column(Boolean, default=True)
    email_newfeatures = Column(Boolean, default=True)
    email_newgifts = Column(Boolean, default=True)
    email_weeklyreport = Column(Boolean, default=True)

    # Device Notifications
    device_allnotifications = Column(Boolean, default=True)
    device_newlikes = Column(Boolean, default=True)
    device_newcomments = Column(Boolean, default=True)
    device_onlynewnoty = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now(), server_default=func.now())

    # Optional: if you want backref to user
    # user = relationship("InjustifyUser", back_populates="notification_settings", uselist=False)



from starlette.middleware.sessions import SessionMiddleware
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from werkzeug.security import check_password_hash, generate_password_hash


from sqladmin.authentication import AuthenticationBackend

# -------------------- Auth Backend --------------------
class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        db = SessionLocal()
        user = db.query(AdminUser).filter_by(username=username).first()
        db.close()

        if user and check_password_hash(user.password_hash, password):
            request.session["user"] = user.username
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("user"))

# -------------------- FastAPI Setup --------------------
app = FastAPI()
import os
media_directory = "static"
os.makedirs(media_directory, exist_ok=True)
app.mount("/static", StaticFiles(directory=media_directory), name="static")
app.add_middleware(SessionMiddleware, secret_key=Config.SECRET_KEY)

def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# -------------------- Admin Panel Setup --------------------
# admin = Admin(app, engine, title="Injustify Admin", logo_url="/static/logo.png",authentication_backend=AdminAuth(432413))
admin = Admin(app, engine, title="Injustify Admin", logo_url="/static/injustify.png")


class VisitorTrackingView(ModelView, model=VisitorTracking):
    column_list =  [VisitorTracking.ip,VisitorTracking.device,VisitorTracking.continent,VisitorTracking.country,VisitorTracking.city]
    column_sortable_list = [VisitorTracking.created_at, VisitorTracking.device, VisitorTracking.ip]
    column_default_sort = (VisitorTracking.created_at, True)
    category = "users"

# -------------------- Admin Views --------------------
class AdminUserView(ModelView, model=AdminUser):
    column_list = [AdminUser.id, AdminUser.username, AdminUser.is_superadmin]
    column_sortable_list = [AdminUser.id]
    column_searchable_list = [AdminUser.username]
    category = "Users"

class ViewModelView(ModelView, model=View):
    column_list = [View.user_id, View.song_id, View.view_count, View.last_viewed]
    column_sortable_list = [View.last_viewed]
    column_default_sort = (View.last_viewed, True)
    category = "Activity"

class DownloadModelView(ModelView, model=Download):
    column_list = [
        Download.download_id, Download.user_id, Download.song_id,Download.file_name,
        Download.download_status, Download.timestamp
    ]
    column_sortable_list = [Download.timestamp]
    column_default_sort = (Download.timestamp, True)
    column_searchable_list = [Download.user_id, Download.song_id]
    category = "Activity"

class InjustifyUserView(ModelView, model=InjustifyUser):
    column_list = [InjustifyUser.email, InjustifyUser.name, InjustifyUser.status, InjustifyUser.created_at]
    column_sortable_list = [InjustifyUser.created_at]
    column_searchable_list = [InjustifyUser.email, InjustifyUser.name]
    category = "Users"

class InjustifyMusicView(ModelView, model=InjustifyMusic):
    column_list = [InjustifyMusic.song_id, InjustifyMusic.title, InjustifyMusic.artist, InjustifyMusic.upload_date]
    column_sortable_list = [InjustifyMusic.upload_date]
    column_searchable_list = [InjustifyMusic.title, InjustifyMusic.artist]
    category = "Music"

class PlaylistView(ModelView, model=Playlist):
    column_list = [Playlist.playlist_id, Playlist.name, Playlist.created_by, Playlist.created_at]
    column_sortable_list = [Playlist.created_at]
    column_default_sort = (Playlist.created_at, True)
    column_searchable_list = [Playlist.name]
    category = "Music"

class PlaylistSongView(ModelView, model=PlaylistSong):
    column_list = [PlaylistSong.playlist_id, PlaylistSong.song_id, PlaylistSong.added_at]
    column_sortable_list = [PlaylistSong.added_at]
    column_default_sort = (PlaylistSong.added_at, True)
    category = "Music"

class VerificationSessionView(ModelView, model=VerificationSession):
    column_list = [VerificationSession.email, VerificationSession.token, VerificationSession.expires_at]
    column_sortable_list = [VerificationSession.expires_at]
    column_default_sort = (VerificationSession.expires_at, False)
    category = "Users"


class NotificationSettingView(ModelView, model=NotificationSetting):
    column_list = [
        NotificationSetting.user_id,
        # "username",  # This is our custom property
    ]

    # column_sortable_list = [NotificationSetting.user_id]
    # column_searchable_list = [NotificationSetting.user_id]
    # category = "Settings"

    # def _username_formatter(self, obj):
    #     return obj.user.name if obj.user else "—"

    # column_formatters = {
    #     "username": _username_formatter
    # }




# -------------------- Register Views --------------------
admin.add_view(AdminUserView)
admin.add_view(VisitorTrackingView)
admin.add_view(ViewModelView)
admin.add_view(DownloadModelView)
admin.add_view(InjustifyUserView)
admin.add_view(InjustifyMusicView)
admin.add_view(PlaylistView)
admin.add_view(PlaylistSongView)
admin.add_view(VerificationSessionView)
admin.add_view(NotificationSettingView)


# -------------------- Routes --------------------
@app.get("/")
async def home():
    return RedirectResponse(url="/admin")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login")

# -------------------- Run Server --------------------
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
