import re
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import Page, expect

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


def test_open_kinopoisk_homepage(page: Page) -> None:
    """Открытие главной страницы Кинопоиска."""
    open_page(page, BASE_URL)

    expect(page).to_have_url(
        re.compile(r"kinopoisk\.ru")
    )

    expect(
        page.get_by_placeholder(
            "Фильмы, сериалы, персоны"
        )
    ).to_be_visible(timeout=15000)


def test_search_movie_by_full_title(page: Page) -> None:
    """Поиск фильма по полному названию."""
    search_movie(page)

    expect(
        page.get_by_text(
            MOVIE_TITLE,
            exact=True,
        ).first
    ).to_be_visible(timeout=15000)


def test_open_movie_from_search_results(page: Page) -> None:
    """Открытие карточки фильма из результатов поиска."""
    search_movie(page)

    close_modal_if_present(page)

    movie_link = page.locator(
        f'a[href*="/film/{MOVIE_ID}/"]'
    ).first

    expect(movie_link).to_be_visible(timeout=15000)

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


def test_movie_details_displayed(page: Page) -> None:
    """Проверка основной информации в карточке фильма."""
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


def test_filter_movies_by_year(page: Page) -> None:
    """Фильтрация фильмов по году выпуска."""
    open_page(
        page,
        f"{BASE_URL}/s/",
    )

    year_input = page.locator(
        'input[name="m_act[year]"]'
    )

    expect(year_input).to_be_visible(timeout=15000)

    year_input.fill("2014")

    form = year_input.locator("xpath=ancestor::form")

    expect(form).to_have_count(1)

    with page.expect_navigation(
        wait_until="domcontentloaded",
        timeout=30000,
    ):
        form.evaluate(
            "(form) => form.requestSubmit()"
        )

    parsed_url = urlparse(page.url)
    query_params = parse_qs(parsed_url.query)

    assert query_params.get("m_act[year]") == ["2014"], (
        "В URL отсутствует фильтр года 2014. "
        f"Фактический URL: {page.url}"
    )

    results = page.locator("body")

    expect(results).to_contain_text(
        "Результаты поиска",
        timeout=15000,
    )

    expect(results).to_contain_text(
        "2014",
        timeout=15000,
    )


def test_filter_movies_by_rating(page: Page) -> None:
    """KP-UI-006: Фильтрация фильмов по рейтингу."""

    # Открываем навигатор по лучшим фильмам.
    open_page(
        page,
        f"{BASE_URL}/top/navigator/",
    )

    # Находим ползунок рейтинга Кинопоиска.
    rating_slider = page.locator("#ratingrange")
    expect(rating_slider).to_be_visible(timeout=15000)

    # Левый бегунок отвечает за минимальный рейтинг.
    min_handle = rating_slider.locator(
        ".ui-slider-handle"
    ).first

    expect(min_handle).to_be_visible(timeout=15000)

    # Начальный рейтинг — 6.
    # Один шаг клавиатуры изменяет рейтинг на 0.1.
    # Устанавливаем минимальный рейтинг 8.
    min_handle.focus()

    for _ in range(20):
        min_handle.press("ArrowRight")

    # Находим кнопку применения фильтра.
    show_movies = page.get_by_text(
        "показать фильмы",
        exact=False,
    ).first

    expect(show_movies).to_be_visible(timeout=15000)

    # Применяем фильтр.
    show_movies.click()

    # Ожидаем изменения URL после применения фильтра.
    expect(page).to_have_url(
        re.compile(r"/top/navigator/m_act"),
        timeout=30000,
    )

    # Раскодируем параметры адреса.
    decoded_url = page.url

    for _ in range(2):
        decoded_url = unquote(decoded_url)

    # Извлекаем минимальный рейтинг из URL.
    rating_match = re.search(
        r"/m_act\[rating\]/([^/]+)",
        decoded_url,
    )

    assert rating_match is not None, (
        "В URL отсутствует параметр рейтинга. "
        f"Фактический URL: {page.url}"
    )

    min_rating = rating_match.group(1).split(":")[0]

    assert float(min_rating) == 8.0, (
        "Ожидался минимальный рейтинг 8, "
        f"но получен {min_rating}. "
        f"Фактический URL: {page.url}"
    )

    # Проверяем появление результатов поиска.
    expect(
        page.get_by_text("Результаты поиска").first
    ).to_be_visible(timeout=15000)

    # Находим блоки с рейтингами фильмов.
    ratings = page.locator(
        "#itemList .ratingGreenBG"
    )

    expect(ratings.first).to_be_visible(timeout=15000)

    rating_count = ratings.count()

    assert rating_count > 0, (
        "В результатах поиска не найдены рейтинги"
    )

    # Проверяем рейтинг каждого найденного фильма.
    for index in range(rating_count):
        rating_text = ratings.nth(index).locator(
            "span"
        ).first.inner_text().strip()

        match = re.match(
            r"^\s*(\d{1,2}[.,]\d+)",
            rating_text,
        )

        assert match is not None, (
            f"Некорректный формат рейтинга: {rating_text!r}"
        )

        rating = float(
            match.group(1).replace(",", ".")
        )

        assert 8 <= rating <= 10, (
            f"Рейтинг {rating} не соответствует "
            "выбранному диапазону 8–10"
        )

    print(
        "KP-UI-006: фильтрация по рейтингу "
        "8–10 выполнена успешно"
    )
