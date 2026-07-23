# Enterprise Backend Architecture & Security Manual

## 1. System Overview
The `injustify_backend` platform is a production-grade, asynchronous Python backend powered by **FastAPI**, **SQLAlchemy 2.0**, and **python-socketio**. It provides real-time media streaming, user management, background job processing, external **Deriv API** monitoring, and a secure **Web Administration Interface**.

```
+-----------------------------------------------------------------------+
|                      Clients & Web Browsers                           |
+-----------------------------------+-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|   REST API Requests   |                       | Socket.IO WebSockets  |
| (/api/v1/admin, etc)  |                       |  (/inj-user, /ws)     |
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
            +-----------------------------------------------+
            |            Security Middleware Layer          |
            | (Security Headers, Rate Limiting, RBAC JWT)   |
            +-----------------------+-----------------------+
                                    |
                                    v
            +-----------------------------------------------+
            |               Application Services            |
            | (Audit Service, Deriv Monitor, WS Tracker)    |
            +-----------------------+-----------------------+
                                    |
                                    v
            +-----------------------------------------------+
            |        SQLAlchemy 2.0 ORM Database Layer      |
            |      (MySQL / PostgreSQL / SQLite Fallback)    |
            +-----------------------------------------------+
```

---

## 2. Core Architectural Principles

### Module Separation
- **`config.py`**: Centralized environment-driven configuration with sanitized diagnostic exposure.
- **`database.py`**: Unified SQLAlchemy 2.0 engine, connection pool, and `get_db` dependency.
- **`models.py`**: Complete ORM schema covering users, admins, audit logs, support tickets, feature flags, and Deriv account links.
- **`services/`**: Decoupled domain services (`audit_service`, `deriv_service`, `websocket_manager`).
- **`middleware/`**: Security headers, rate limiting, and Role-Based Access Control (RBAC).
- **`routes/admin_api.py`**: RESTful admin endpoints with validation schemas and standardized JSON responses.
- **`static/admin/`**: Zero-dependency Web Administration Interface (SPA).

---

## 3. Security Architecture & FinTech Boundaries

### Role-Based Access Control (RBAC)
Administrators are assigned granular roles:
- **`superadmin`**: Unrestricted access to user role management, system settings, feature flags, and audit logs.
- **`admin`**: Access to user status updates, support tickets, and system monitoring.
- **`support`**: Access to view support tickets, add internal notes, and inspect non-sensitive user profile metadata.
- **`auditor`**: Read-only access to audit logs, authentication logs, and API performance metrics.

### FinTech Security Boundaries
1. **Zero Access to Credentials**: Administrators cannot view, decrypt, or export raw user passwords or Deriv OAuth secrets.
2. **No Impersonation / Execution**: Admins are strictly prohibited from executing trades or mutating trading parameters on behalf of users.
3. **Mandatory Audit Trailing**: Every privileged action (e.g. user status change, role update, feature flag toggle) automatically generates an immutable record in `audit_logs`.
