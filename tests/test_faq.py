def test_faq_page_loads(client):
    """Check that FAQ page loads successfully and has common questions."""
    response = client.get('/faq')
    assert response.status_code == 200
    data = response.data.decode("utf-8")
    assert "Frequently Asked Questions" in data
    assert "How do I resolve errors" in data  # one of your FAQ questions
