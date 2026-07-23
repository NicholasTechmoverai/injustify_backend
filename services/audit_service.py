import logging
import time
from sqlalchemy.orm import Session
from models import AuditLog, AuthLog, APILog

logger = logging.getLogger("audit_service")

def log_audit_action(
    db: Session,
    actor_username: str,
    actor_role: str,
    action: str,
    category: str,
    target_resource: str = None,
    details: str = None,
    ip_address: str = None,
    status: str = "SUCCESS"
):
    """ Logs a privileged administrator action for compliance and audit trailing """
    try:
        log_entry = AuditLog(
            actor_username=actor_username,
            actor_role=actor_role,
            action=action,
            category=category,
            target_resource=target_resource,
            details=details,
            ip_address=ip_address,
            status=status
        )
        db.add(log_entry)
        db.commit()
        logger.info(f"AUDIT LOG [{category}] {action} by {actor_username} ({actor_role}) -> {target_resource or 'N/A'}")
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        db.rollback()

def log_auth_event(
    db: Session,
    username: str,
    event_type: str,
    ip_address: str = None,
    user_agent: str = None,
    status: str = "SUCCESS",
    failure_reason: str = None
):
    """ Logs authentication events (login, logout, failed login) """
    try:
        auth_entry = AuthLog(
            username=username,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            failure_reason=failure_reason
        )
        db.add(auth_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record auth log: {e}")
        db.rollback()

def log_api_request(
    db: Session,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    ip_address: str = None
):
    """ Logs API request metrics """
    try:
        api_entry = APILog(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address
        )
        db.add(api_entry)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record API request log: {e}")
        db.rollback()
