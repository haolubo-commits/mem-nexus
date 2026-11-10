"""
Pytest fixtures and configuration for MemNexus.
"""

import sys
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.db.mongodb import db_manager


@pytest.fixture(scope="session", autouse=True)
def setup_app_lifecycle():
    # Lifespan startup and shutdown
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(setup_app_lifecycle) -> Generator[TestClient, None, None]:
    yield setup_app_lifecycle

