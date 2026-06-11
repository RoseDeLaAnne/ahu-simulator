from app.ui.concept03.page_router import DEFAULT_PAGE
from app.ui.concept03.shell import build_concept03_shell


def test_shell_builds_regions_in_tab_order() -> None:
    shell = build_concept03_shell()

    assert shell.id == "concept03-shell"
    assert shell.children[0].id == "app-header"
    # concept03-page-content replaces central-canvas as the center grid area wrapper
    expected_ids = [
        "app-header", "left-rail", "concept03-page-content",
        "right-rail", "bottom-strip", "app-footer-nav",
    ]
    assert [child.id for child in shell.children] == expected_ids
    assert [child.tabIndex for child in shell.children] == [0, 0, 0, 0, 0, 0]


def test_shell_uses_default_page_for_unknown_page() -> None:
    shell = build_concept03_shell(active_page="unknown")

    assert shell.to_plotly_json()["props"]["data-active-page"] == DEFAULT_PAGE.value


def test_shell_has_phase1_placeholders() -> None:
    shell = build_concept03_shell()
    placeholder_text = str(shell.to_plotly_json())

    assert placeholder_text.count("coming soon") == 5
    assert "ЦЕНТРАЛЬНЫЙ CANVAS" in placeholder_text
