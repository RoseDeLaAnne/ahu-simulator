from app.ui.concept03.page_router import DEFAULT_PAGE, PAGE_IDS, select_page


def test_select_page_defaults_to_dashboard() -> None:
    assert select_page(None) == DEFAULT_PAGE.value
    assert select_page("") == DEFAULT_PAGE.value
    assert select_page("?theme=concept03") == DEFAULT_PAGE.value


def test_select_page_accepts_known_concept03_pages() -> None:
    for page_id in PAGE_IDS:
        assert select_page(f"?theme=concept03&page={page_id}") == page_id


def test_select_page_rejects_unknown_or_legacy_pages() -> None:
    assert select_page("?page=service-index") == DEFAULT_PAGE.value
    assert select_page("?page=../../settings") == DEFAULT_PAGE.value
