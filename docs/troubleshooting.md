# Troubleshooting & Diagnostics Guide

## 1. Database Issues
- **Symptom**: `OperationalError: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")`
- **Resolution**: The system automatically falls back to SQLite (`mydb.sqlite`) if MySQL is unavailable. Check `database.py` logs to confirm fallback status.

## 2. Authentication Failures
- **Symptom**: `401 Unauthorized - Invalid or expired admin token`
- **Resolution**: JWT tokens expire after 8 hours. Re-authenticate at `/admin-ui` using admin credentials.

## 3. WebSocket Disconnections
- **Symptom**: Socket.IO client fails to connect to `/inj-user` or `/ws`
- **Resolution**: Ensure Nginx or reverse proxy has WebSocket upgrade headers configured (`Upgrade` and `Connection` headers).
