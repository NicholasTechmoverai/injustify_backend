# Environment Configuration & Secret Management Guide

## 1. Environment Variables

Configure the following variables in a `.env` file at the root of the project:

```env
# Application Settings
ENVIRONMENT=production
SECRET_KEY=injustify_super_secret_enterprise_key_2026
JWT_SECRET=injustify_jwt_admin_secret_key_998877

# Network & Server URLs
BACKEND_SERVER=http://127.0.0.1:5000
FRONTEND_SERVER=http://localhost:8080

# Database Configuration (MySQL / PostgreSQL / SQLite)
DATABASE_URL=mysql+pymysql://root:0000@localhost/injustify
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=0000
DB_NAME=injustify

# Deriv Integration Settings
DERIV_APP_ID=1089
DERIV_WS_URL=wss://ws.derivws.com/websockets/v3

# OAuth Configuration
MY_ID=your_google_client_id
MY_SECRET=your_google_client_secret
```

---

## 2. Secret Protection

> [!IMPORTANT]
> Never commit `.env` or hardcoded credentials to git repositories.
> - The `Config.get_sanitized_config()` method masks all secret keys and returns only non-sensitive diagnostics to the Admin UI.
