"""
conftest.py — Shared fixtures for ETECSA Asset Sync test suite.
"""

import pytest
from django.test import Client
from django.contrib.auth.models import User


@pytest.fixture
def client():
    """Provide a Django test client."""
    return Client()


@pytest.fixture
def auth_client(client, db):
    """Provide an authenticated Django test client."""
    user = User.objects.create_user(username="testuser", password="testpass123")
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def sample_user(db):
    """Create a sample user for testing."""
    return User.objects.create_user(
        username="operator", password="secure123", email="op@etecsa.cu"
    )
