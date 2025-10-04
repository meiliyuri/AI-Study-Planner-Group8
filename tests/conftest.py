import os
import sys

import pytest

# Ensure your app folder is in the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app  # import the app instance directly


@pytest.fixture
def client():
    # Enable testing mode
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
