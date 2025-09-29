from bs4 import BeautifulSoup

def test_export_pdf_button_exists(client):
    """Check that Export PDF button exists and is initially disabled."""
    response = client.get('/planner')
    soup = BeautifulSoup(response.data, 'html.parser')
    export_btn = soup.find(id="export-pdf")
    assert export_btn is not None
    assert "Export PDF" in export_btn.text
    assert export_btn.has_attr("disabled")
