import re

from urllib.parse import parse_qs, urlparse
from playwright.sync_api import (
    Page,
    expect,
    sync_playwright,
)

BASE_URL = "https://www.kinopoisk.ru"
MOVIE_ID = 258687
MOVIE_TITLE = "Интерстеллар"
MOVIE_URL = f"{BASE_URL}/film/{MOVIE_ID}/"


def open_page(page: Page, url: str) -> None:
    """Открыть страницу и дождаться загрузки HTML."""
    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=30000,
    )


def close_modal_if_present(page: Page) -> None:
    """Закрыть модальное окно, если оно появилось."""
    overlay = page.locator(".ReactModal__Overlay")

    try:
        overlay.first.wait_for(
            state="visible",
            timeout=1500,
        )
    except Exception:
        return

    close_button = overlay.first.get_by_role(
        "button",
        name=re.compile("закрыть", re.IGNORECASE),
    )

    if close_button.count() > 0:
        close_button.first.click()
        expect(overlay.first).to_be_hidden(
            timeout=5000
        )
    else:
        raise AssertionError(
            "Модальное окно перекрывает страницу, "
            "но кнопка закрытия не найдена"
        )


def search_movie(page: Page) -> None:
    """Найти фильм через поисковую строку."""
    open_page(page, BASE_URL)

    search = page.get_by_placeholder(
        "Фильмы, сериалы, персоны"
    )

    expect(search).to_be_visible(timeout=15000)

    search.fill(MOVIE_TITLE)
    search.press("Enter")

    page.wait_for_url(
        "**/new-search/?text=*",
        timeout=30000,
    )

    expect(
        page.get_by_text(
            MOVIE_TITLE,
            exact=True,
        ).first
    ).to_be_visible(timeout=15000)


def test_open_kinopoisk_homepage() -> None:
    """KP-UI-001: Открытие главной страницы."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:
            open_page(page, BASE_URL)

            expect(page).to_have_url(
                re.compile(r"kinopoisk\.ru")
            )

            expect(
                page.get_by_placeholder(
                    "Фильмы, сериалы, персоны"
                )
            ).to_be_visible(timeout=15000)

        finally:
            browser.close()


def test_search_movie_by_full_title() -> None:
    """KP-UI-002: Поиск фильма по названию."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:
            search_movie(page)

            expect(
                page.get_by_text(
                    MOVIE_TITLE,
                    exact=True,
                ).first
            ).to_be_visible(timeout=15000)

        finally:
            browser.close()


def test_open_movie_from_search_results() -> None:
    """KP-UI-003: Открытие карточки из поиска."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:
            search_movie(page)

            close_modal_if_present(page)

            movie_link = page.locator(
                f'a[href*="/film/{MOVIE_ID}/"]'
            ).first

            expect(movie_link).to_be_visible(
                timeout=15000
            )

            movie_link.click()

            page.wait_for_url(
                f"**/film/{MOVIE_ID}/**",
                timeout=30000,
            )

            expect(
                page.get_by_role(
                    "heading",
                    name=re.compile(MOVIE_TITLE),
                ).first
            ).to_be_visible(timeout=15000)

        finally:
            browser.close()


def test_movie_details_displayed() -> None:
    """KP-UI-004: Проверка карточки фильма."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        try:
            open_page(page, MOVIE_URL)

            expect(page).to_have_url(
                re.compile(r"/film/258687/")
            )

            expect(
                page.get_by_role(
                    "heading",
                    name=re.compile(MOVIE_TITLE),
                ).first
            ).to_be_visible(timeout=15000)

            expect(
                page.get_by_text(
                    "2014",
                    exact=True,
                ).first
            ).to_be_visible(timeout=15000)

            expect(
                page.get_by_text(
                    "О фильме",
                    exact=True,
                ).first
            ).to_be_visible(timeout=15000)

            expect(
                page.get_by_text(
                    "Жанр",
                    exact=True,
                ).first
            ).to_be_visible(timeout=15000)

        finally:
            browser.close()


def test_filter_movies_by_year() -> None:
    """KP-UI-005: Фильтрация фильмов по году выпуска."""

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Открываем расширенный поиск Кинопоиска
            page.goto(
                "https://www.kinopoisk.ru/s/",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Находим поле года выпуска
            year_input = page.locator(
                'input[name="m_act[year]"]'
            )

            expect(year_input).to_be_visible(
                timeout=15000
            )

            # Устанавливаем год
            year_input.fill("2014")

            # Отправляем форму расширенного поиска
            form = year_input.locator("xpath=ancestor::form")

            expect(form).to_have_count(1)

            with page.expect_navigation(
                wait_until="domcontentloaded",
                timeout=30000,
            ):
                form.evaluate(
                    "(form) => form.requestSubmit()"
                )

            # Проверяем фактический адрес
            print("URL после фильтрации:", page.url)

            parsed_url = urlparse(page.url)
            query_params = parse_qs(parsed_url.query)

            # Проверяем, что выбранный год
            # передан в параметрах запроса
            assert query_params.get(
                "m_act[year]"
            ) == ["2014"], (
                "В URL отсутствует фильтр года 2014. "
                f"Фактический URL: {page.url}"
            )

            # Проверяем наличие результатов
            results = page.locator("body")

            expect(results).to_contain_text(
                "Результаты поиска",
                timeout=15000,
            )

            # Проверяем наличие фильмов 2014 года
            expect(results).to_contain_text(
                "2014",
                timeout=15000,
            )

            print(
                "KP-UI-005: фильтрация по году "
                "2014 выполнена успешно"
            )

        finally:
            browser.close()
