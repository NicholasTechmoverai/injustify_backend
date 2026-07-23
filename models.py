import datetime
from sqlalchemy import (
    Column, Integer, String, TIMESTAMP, Enum,
    BigInteger, Text, Boolean, Date, Float, ForeignKey, Time, func
)
from sqlalchemy.orm import relationship
from database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="admin", nullable=False) # superadmin, admin, support, auditor
    is_superadmin = Column(Boolean, default=False)
    status = Column(String(20), default="active") # active, suspended
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)

class InjustifyUser(Base):
    __tablename__ = "injustifyusers"
    id = Column(String(36), primary_key=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    picture = Column(String(855), nullable=True)
    verified_email = Column(Boolean, default=False)
    password = Column(String(255), nullable=True)
    role = Column(String(50), default="user") # user, premium_user
    status = Column(String(20), default="active") # active, suspended
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP, nullable=True)
    notification_setting = relationship("NotificationSetting", back_populates="user", uselist=False)

class VisitorTracking(Base):
    __tablename__ = "visitor_tracking"
    id = Column(Integer, primary_key=True, autoincrement=True)
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
    created_at = Column(TIMESTAMP, server_default=func.now())

class View(Base):
    __tablename__ = "views"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(36), index=True)
    song_id = Column(String(10), index=True)
    view_count = Column(Integer, default=1)
    progress = Column(Float, default=0.00)
    last_viewed = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Download(Base):
    __tablename__ = "downloads"
    download_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, index=True)
    song_id = Column(String(36), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_format = Column(String(50), nullable=False)
    itag = Column(String(50), nullable=False)
    downloaded_size = Column(BigInteger, nullable=False, default=0)
    file_size = Column(BigInteger, nullable=False)
    file_source = Column(String(50), nullable=False)
    download_status = Column(String(20), default="IN_PROGRESS") # SUCCESS, FAILED, IN_PROGRESS
    user_agent = Column(Text, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    retries = Column(Integer, default=0)
    failure_reason = Column(Text, nullable=True)
    is_partial = Column(Boolean, default=False)
    thumbnail = Column(String(255), nullable=False)

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
    upload_date = Column(TIMESTAMP, server_default=func.now())
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
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class PlaylistSong(Base):
    __tablename__ = "playlistsongs"
    playlist_song_id = Column(Integer, primary_key=True, autoincrement=True)
    playlist_id = Column(String(10), nullable=False)
    song_id = Column(String(10), nullable=False)
    added_at = Column(TIMESTAMP, server_default=func.now())

class VerificationSession(Base):
    __tablename__ = "verification_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True)
    expires_at = Column(TIMESTAMP, nullable=False)

class NotificationSetting(Base):
    __tablename__ = "notification_settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("injustifyusers.id", ondelete="CASCADE"), nullable=False)
    user = relationship("InjustifyUser", back_populates="notification_setting", uselist=False)

    enable_sound_alerts = Column(Boolean, default=False)
    selected_sound = Column(String(100), nullable=True)
    do_not_disturb = Column(Boolean, default=False)

    dnd_start_time = Column(Time, nullable=True)
    dnd_end_time = Column(Time, nullable=True)

    dnd_allow_calls = Column(Boolean, default=False)
    dnd_allow_messages = Column(Boolean, default=False)
    dnd_allow_urgent = Column(Boolean, default=False)

    email_newsignin = Column(Boolean, default=True)
    email_newfeatures = Column(Boolean, default=True)
    email_newgifts = Column(Boolean, default=True)
    email_weeklyreport = Column(Boolean, default=True)

    device_allnotifications = Column(Boolean, default=True)
    device_newlikes = Column(Boolean, default=True)
    device_newcomments = Column(Boolean, default=True)
    device_onlynewnoty = Column(Boolean, default=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

# --- Enterprise Admin & System Management Models ---

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_username = Column(String(100), nullable=False, index=True)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False) # e.g. USER_SUSPENDED, ROLE_UPDATED, CONFIG_CHANGED
    category = Column(String(50), nullable=False, index=True) # SECURITY, USER_MGMT, CONFIG, SYSTEM
    target_resource = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    status = Column(String(20), default="SUCCESS") # SUCCESS, FAILED
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)

class AuthLog(Base):
    __tablename__ = "auth_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), nullable=False, index=True)
    event_type = Column(String(50), nullable=False) # LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT, TOKEN_REFRESH
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    status = Column(String(20), default="SUCCESS")
    failure_reason = Column(String(255), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)

class APILog(Base):
    __tablename__ = "api_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Float, nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(36), unique=True, nullable=False, index=True)
    user_email = Column(String(255), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="GENERAL") # BILLING, TECHNICAL, DERIV_ACCOUNT, GENERAL
    status = Column(String(20), default="OPEN") # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    priority = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, URGENT
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class TicketNote(Base):
    __tablename__ = "ticket_notes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False)
    author = Column(String(100), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

class SystemConfig(Base):
    __tablename__ = "system_configs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    data_type = Column(String(20), default="string") # string, number, boolean, json
    description = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    id = Column(Integer, primary_key=True, autoincrement=True)
    flag_name = Column(String(100), unique=True, nullable=False, index=True)
    is_enabled = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DerivAccount(Base):
    __tablename__ = "deriv_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("injustifyusers.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(50), nullable=False, unique=True)
    currency = Column(String(10), default="USD")
    balance = Column(Float, default=0.0)
    account_type = Column(String(20), default="demo") # demo, real
    status = Column(String(20), default="connected") # connected, disconnected, suspended
    connected_at = Column(TIMESTAMP, server_default=func.now())
    last_synced_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
