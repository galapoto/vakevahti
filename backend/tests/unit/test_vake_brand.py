from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ui.brand import VAKE_COLORS, VAKE_FONT_FAMILY


def test_dashboard_uses_official_vake_poppins_typography() -> None:
    app = create_app(Settings(dashboard_preview_mode=True))
    response = TestClient(app).get("/")

    assert response.status_code == 200
    html = response.text
    assert 'family=Poppins:wght@300;400;600;700' in html
    assert '--vake-font: "Poppins", Calibri, Arial, sans-serif' in html
    assert "font-family: var(--vake-font)" in html


def test_dashboard_exposes_canonical_vake_palette() -> None:
    app = create_app(Settings(dashboard_preview_mode=True))
    response = TestClient(app).get("/")

    assert response.status_code == 200
    html = response.text.upper()
    for color in (
        "#312783",
        "#76CBF3",
        "#00983A",
        "#74B72B",
        "#E6007E",
        "#EA5297",
    ):
        assert color in html


def test_brand_tokens_are_reusable_by_report_and_email_renderers() -> None:
    assert "Poppins" in VAKE_FONT_FAMILY
    assert VAKE_COLORS["purple"] == "#312783"
    assert VAKE_COLORS["fuchsia"] == "#E6007E"
