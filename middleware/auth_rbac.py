import time
import jwt
from typing import List
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import Config
from database import get_db
from models import AdminUser
from werkzeug.security import generate_password_hash, check_password_hash

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, plain_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = time.time() + (Config.JWT_EXPIRE_MINUTES * 60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return decoded
    except Exception:
        return None

def get_current_admin(
    request: Request,
    auth: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> AdminUser:
    """ Retrieves and validates current admin user from JWT header or Session cookie """
    token = None
    
    # 1. Try Bearer token
    if auth and auth.credentials:
        token = auth.credentials
    
    # 2. Try Session cookie or header fallback
    if not token:
        token = request.headers.get("X-Admin-Token") or request.session.get("admin_token")
    
    if not token:
        # Fallback to session username if logged in via standard web form
        session_user = request.session.get("user")
        if session_user:
            admin = db.query(AdminUser).filter(AdminUser.username == session_user).first()
            if admin and admin.status == "active":
                return admin

        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token.")

    username = payload["sub"]
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    
    if not admin:
        raise HTTPException(status_code=401, detail="Administrator account not found.")
    
    if admin.status != "active":
        raise HTTPException(status_code=403, detail="Administrator account is suspended.")

    return admin

def require_roles(allowed_roles: List[str]):
    """ Dependency factory for enforcing RBAC permissions """
    def role_checker(current_admin: AdminUser = Depends(get_current_admin)):
        if current_admin.is_superadmin or current_admin.role in allowed_roles:
            return current_admin
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Required role: {', '.join(allowed_roles)}"
        )
    return role_checker
