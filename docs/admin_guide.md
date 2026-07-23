# Administration Interface User Guide

## 1. Accessing the Interface
Navigate to `http://<server-host>:5000/admin-ui` or `http://<server-host>:5000/admin`.

### Default Credentials
- **Username**: `admin`
- **Password**: `AdminPass123!`

---

## 2. Platform Modules

### Dashboard Overview
- Monitors CPU, RAM, and Disk metrics in real time.
- Displays active platform users, linked Deriv demo & real accounts, active Socket.IO connections, and average API latency.
- Features a live recent activity feed.

### User Management
- Filter users by status (`active`, `suspended`) or role (`user`, `premium_user`).
- Click the eye icon to view user profile details and connected Deriv accounts.
- Click **Suspend** or **Reactivate** to update account status. All status changes are logged to the audit center.

### System Monitoring
- Displays live health indicators for API Service, Database, Deriv API WebSocket, Socket.IO Server, Cache, Background Workers, and Cron Jobs.

### Logs & Audit Center
- Multi-tab viewer for **Audit Log**, **Auth Events**, **API Metrics**, and **Security Alerts**.
- Export log records to CSV or JSON format using the header action buttons.

### System Config & Feature Flags
- Toggle platform-wide **Maintenance Mode**.
- Enable/disable feature flags in real time.
- Review sanitized environment diagnostics.

### Support Center
- Manage user support requests, update ticket status, and attach internal staff notes.
