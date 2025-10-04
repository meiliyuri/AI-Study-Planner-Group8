def test_home_page(client):
    """Test if home page loads successfully"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Study Plan" in response.data  # Adjust text based on your page content


def test_admin_page(client):
    """Test if admin login/admin panel page loads successfully"""
    response = client.get("/admin")
    assert response.status_code == 200
    assert b"Admin Panel" in response.data
