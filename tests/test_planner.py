

from bs4 import BeautifulSoup

def test_generate_plan_buttons_disabled(client):
    """Check that Generate/AI/Export buttons are initially disabled."""
    response = client.get('/planner')
    soup = BeautifulSoup(response.data, 'html.parser')

    generate_btn = soup.find(id="generate-plan")
    ai_btn = soup.find(id="ai-validate-plan")
    export_btn = soup.find(id="export-pdf")

    assert generate_btn is not None
    assert ai_btn is not None
    assert export_btn is not None

    # Check if buttons have 'disabled' attribute
    assert generate_btn.has_attr('disabled')
    assert ai_btn.has_attr('disabled')
    assert export_btn.has_attr('disabled')
