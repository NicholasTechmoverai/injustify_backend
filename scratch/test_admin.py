import os
import sys
import unittest
import asyncio
from fastapi.testclient import TestClient

# Ensure root dir is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from appp import app, on_startup
from database import engine, Base, SessionLocal
from models import AdminUser, InjustifyUser, DerivAccount, FeatureFlag
from middleware.auth_rbac import hash_password

class TestAdminArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create database tables and seed test data
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            if not db.query(AdminUser).filter(AdminUser.username == "admin").first():
                db.add(AdminUser(
                    username="admin",
                    email="admin@injustify.com",
                    password_hash=hash_password("AdminPass123!"),
                    role="superadmin",
                    is_superadmin=True,
                    status="active"
                ))
            if not db.query(InjustifyUser).filter(InjustifyUser.id == "u_demo_101").first():
                db.add(InjustifyUser(
                    id="u_demo_101",
                    name="Enterprise Trader",
                    email="trader@injustify.com",
                    status="active",
                    role="user"
                ))
            if not db.query(FeatureFlag).filter(FeatureFlag.flag_name == "maintenance_mode").first():
                db.add(FeatureFlag(flag_name="maintenance_mode", is_enabled=False, description="Maintenance State"))
            db.commit()
        finally:
            db.close()

        cls.client = TestClient(app)

    def test_01_admin_login(self):
        response = self.client.post("/api/v1/admin/auth/login", json={
            "username": "admin",
            "password": "AdminPass123!"
        })
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["admin"]["role"], "superadmin")
        TestAdminArchitecture.token = data["access_token"]

    def test_02_dashboard_stats(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        response = self.client.get("/api/v1/admin/dashboard/stats", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("metrics", data)
        self.assertIn("health_status", data)
        self.assertIn("resources", data)

    def test_03_user_management(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        response = self.client.get("/api/v1/admin/users", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("users", data)
        self.assertGreater(len(data["users"]), 0)

        # Test user status toggle
        user_id = data["users"][0]["id"]
        status_res = self.client.put(f"/api/v1/admin/users/{user_id}/status", headers=headers, json={
            "status": "suspended",
            "reason": "Test suspension"
        })
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["new_status"], "suspended")

        # Reactivate
        reactivate_res = self.client.put(f"/api/v1/admin/users/{user_id}/status", headers=headers, json={
            "status": "active",
            "reason": "Test reactivation"
        })
        self.assertEqual(reactivate_res.status_code, 200)

    def test_04_system_monitoring(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        response = self.client.get("/api/v1/admin/monitoring", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("services", data)

    def test_05_logs_and_audit(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        response = self.client.get("/api/v1/admin/logs?log_type=audit", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("logs", data)
        self.assertGreater(len(data["logs"]), 0)

    def test_06_configuration_sanitization(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        response = self.client.get("/api/v1/admin/config", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Verify secrets are NOT exposed
        raw_text = response.text
        self.assertNotIn("injustify_super_secret", raw_text)
        self.assertNotIn("injustify_jwt_admin", raw_text)
        self.assertIn("system_configuration", data)
        self.assertIn("feature_flags", data)

    def test_07_support_tickets(self):
        headers = {"Authorization": f"Bearer {TestAdminArchitecture.token}"}
        # Create ticket
        create_res = self.client.post("/api/v1/admin/support/tickets", headers=headers, json={
            "user_email": "user@example.com",
            "subject": "Deriv Sync Inquiry",
            "description": "How do I link my Deriv account?",
            "category": "DERIV_ACCOUNT",
            "priority": "HIGH"
        })
        self.assertEqual(create_res.status_code, 200)
        ticket_id = create_res.json()["id"]

        # List tickets
        list_res = self.client.get("/api/v1/admin/support/tickets", headers=headers)
        self.assertEqual(list_res.status_code, 200)
        self.assertGreater(len(list_res.json()["tickets"]), 0)

        # Add internal note
        note_res = self.client.post(f"/api/v1/admin/support/tickets/{ticket_id}/notes", headers=headers, json={
            "note_text": "Customer contacted via live chat, issue resolved."
        })
        self.assertEqual(note_res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
