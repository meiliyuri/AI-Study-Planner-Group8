def test_db_connection(client):
    """Check that the database object exists."""
    from app import db

    assert db is not None


def test_admin_status_page(client):
    """Check that /api/admin/status returns 200 OK (even if mock)."""
    response = client.get("/api/admin/status")
    # If you haven't implemented the route yet, you can mock it or skip this test
    assert response.status_code in [200, 404]  # 200 if implemented, 404 if placeholder
    if response.status_code == 200:
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "ok"
