import pytest
from playwright.sync_api import Page, sync_playwright


@pytest.fixture
def page() -> Page:
    """Создать отдельную страницу браузера для теста."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        try:
            page = browser.new_page()
            yield page
        finally:
            browser.close()
