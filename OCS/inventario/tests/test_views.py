"""
test_views.py — Integration tests for ETECSA Asset Sync views.

Tests authentication, dashboard rendering, report access,
analytics endpoints, and permission guards.
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from inventario.models import AccountInfo


class TestAuthViews(TestCase):
    """Tests for authentication views (login, register, logout)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_login_page_renders(self):
        """Login page should return 200."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        """Valid credentials should redirect to dashboard."""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("dashboard", response.url)

    def test_login_invalid(self):
        """Invalid credentials should show error."""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 200)

    def test_register_page_renders(self):
        """Registration page should return 200."""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_register_success(self):
        """Successful registration should redirect to dashboard."""
        response = self.client.post(
            reverse("register"),
            {"username": "newuser", "password": "newpass123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_logout_redirects(self):
        """Logout should redirect to login page."""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)


class TestProtectedViews(TestCase):
    """Tests for views that require authentication."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="operator", password="secure123"
        )

    def test_dashboard_requires_login(self):
        """Dashboard should redirect unauthenticated users to login."""
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower() + "?")

    def test_accountinfo_requires_login(self):
        """Asset table should redirect unauthenticated users."""
        response = self.client.get(reverse("accountinfo"))
        self.assertEqual(response.status_code, 302)

    def test_analytics_requires_login(self):
        """Analytics page should redirect unauthenticated users."""
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_renders_when_authenticated(self):
        """Dashboard should render for authenticated users."""
        self.client.login(username="operator", password="secure123")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")

    def test_accountinfo_renders_when_authenticated(self):
        """Asset table should render for authenticated users."""
        self.client.login(username="operator", password="secure123")
        response = self.client.get(reverse("accountinfo"))
        self.assertEqual(response.status_code, 200)

    def test_analytics_renders_when_authenticated(self):
        """Analytics page should render for authenticated users."""
        self.client.login(username="operator", password="secure123")
        response = self.client.get(reverse("analytics"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Analytics")


class TestAPIEndpoints(TestCase):
    """Tests for JSON API endpoints."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="apiuser", password="apipass123"
        )
        self.client.login(username="apiuser", password="apipass123")

    def test_dashboard_stats_api(self):
        """Dashboard stats API should return JSON."""
        response = self.client.get(reverse("api_dashboard_stats"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total", data)
        self.assertIn("with_tag", data)
        self.assertIn("buildings", data)

    def test_analytics_api(self):
        """Analytics API should return JSON with expected structure."""
        response = self.client.get(reverse("api_analytics"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("anomalies", data)
        self.assertIn("data_quality", data)
        self.assertIn("summary", data)

    def test_api_requires_auth(self):
        """API endpoints should reject unauthenticated requests."""
        self.client.logout()
        response = self.client.get(reverse("api_dashboard_stats"))
        self.assertEqual(response.status_code, 302)


class TestReportViews(TestCase):
    """Tests for report-related views."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="reporter", password="report123"
        )
        self.client.login(username="reporter", password="report123")

    def test_no_reports_renders_fallback(self):
        """When no report file exists, should show fallback template."""
        response = self.client.get(reverse("show_reports"))
        self.assertEqual(response.status_code, 200)

    def test_download_logs_no_file(self):
        """Download should redirect when file doesn't exist."""
        response = self.client.get(reverse("download_logs"))
        self.assertEqual(response.status_code, 302)


class TestSyncView(TestCase):
    """Tests for TAG synchronization view."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="syncer", password="sync123"
        )
        self.client.login(username="syncer", password="sync123")

    def test_sync_get_redirects(self):
        """GET request to sync should redirect to accountinfo."""
        response = self.client.get(reverse("sync_tags"))
        self.assertEqual(response.status_code, 302)

    @patch("inventario.views.call_command")
    def test_sync_post_success(self, mock_call):
        """POST to sync should call management command and redirect."""
        mock_call.return_value = None
        response = self.client.post(reverse("sync_tags"))
        self.assertEqual(response.status_code, 302)
        mock_call.assert_called_once_with("sync_tags")

    @patch("inventario.views.call_command")
    def test_sync_post_error(self, mock_call):
        """POST to sync with error should show error message."""
        mock_call.side_effect = Exception("DB connection failed")
        response = self.client.post(reverse("sync_tags"))
        self.assertEqual(response.status_code, 302)
