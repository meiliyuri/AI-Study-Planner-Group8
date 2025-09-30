# tests/test_faq.py
from bs4 import BeautifulSoup

def test_faq_page_loads(client):
    resp = client.get("/faq")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Frequently Asked Questions" in html

def test_faq_has_multiple_questions(client):
    resp = client.get("/faq")
    soup = BeautifulSoup(resp.data, "html.parser")
    h3s = [h.get_text(strip=True).lower() for h in soup.find_all("h3")]
    assert len(h3s) >= 3
    # at least one of your known prompts
    expect_any = [
        "generate plan is disabled",
        "generate plan but it failed",
        "missing prerequisites",
    ]
    assert any(any(s in q for s in expect_any) for q in h3s)
