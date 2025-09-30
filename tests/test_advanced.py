import pytest
from bs4 import BeautifulSoup

# ---------------------------
# Planner Page Tests
# ---------------------------


def test_plan_semester_drop_limits(client):
    """Ensure each semester has a drop-zone with 4-unit max placeholder."""
    response = client.get("/planner")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    drop_zones = soup.find_all("div", class_="drop-zone")
    assert len(drop_zones) >= 6  # 3 years × 2 semesters each
    for dz in drop_zones:
        assert "Drop units here (4 max)" in dz.text


def test_generate_ai_buttons_initially_disabled(client):
    """Generate and AI Validate buttons should be disabled initially."""
    response = client.get("/planner")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    generate_btn = soup.find(id="generate-plan")
    ai_btn = soup.find(id="ai-validate-plan")
    assert generate_btn.has_attr("disabled")
    assert ai_btn.has_attr("disabled")


def test_available_units_and_trash_zone(client):
    """Check if units list and trash zone exist."""
    response = client.get("/planner")
    soup = BeautifulSoup(response.data, "html.parser")
    available_units = soup.find(id="available-units")
    trash_zone = soup.find(id="trash-zone")
    assert available_units is not None
    assert trash_zone is not None
    assert "Drop here to remove" in trash_zone.text


def test_ai_debug_log_and_chat_form(client):
    """Ensure AI debug log and chat form exist on planner page."""
    response = client.get("/planner")
    soup = BeautifulSoup(response.data, "html.parser")
    debug_log = soup.find(id="debug-log")
    chat_form = soup.find(id="ai-chat-form")
    assert debug_log is not None
    assert chat_form is not None
    chat_input = chat_form.find("input", {"id": "ai-chat-input"})
    assert chat_input is not None
    send_btn = chat_form.find("button", type="submit")
    assert send_btn is not None


# ---------------------------
# Admin Page Tests
# ---------------------------


def test_admin_import_form_exists(client):
    """Check that import form and file inputs exist."""
    response = client.get("/admin")
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    import_form = soup.find(id="import-form")
    assert import_form is not None
    file_inputs = import_form.find_all("input", type="file")
    assert len(file_inputs) >= 3  # Units CSV, Units rules CSV, Sequence XLSX


def test_clear_cache_button_exists(client):
    """Check that Clear Cache button exists."""
    response = client.get("/admin")
    soup = BeautifulSoup(response.data, "html.parser")
    clear_btn = soup.find(id="clear-cache")
    assert clear_btn is not None
    assert "Clear Plan Cache" in clear_btn.text


def test_system_status_badges_exist(client):
    """Ensure database and AI status badges are present."""
    response = client.get("/admin")
    soup = BeautifulSoup(response.data, "html.parser")
    db_status = soup.find(id="db-status")
    ai_status = soup.find(id="ai-status")
    assert db_status is not None
    assert ai_status is not None
    assert "Checking..." in db_status.text
    assert "Checking..." in ai_status.text  # Server-rendered default
