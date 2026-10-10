import requests

from config.settings import API_TOKEN, BASE_URL


def test_get_movies_list() -> None:
    """KP-API-001: Получение списка фильмов."""

    assert API_TOKEN, "API_TOKEN не задан в .env"

    response = requests.get(
        f"{BASE_URL}/movie",
        headers={
            "X-API-KEY": API_TOKEN,
            "Accept": "application/json",
        },
        timeout=15,
    )

    assert response.status_code == 200, (
        f"Ожидался статус 200, получен {response.status_code}"
    )

    data = response.json()

    assert "docs" in data, "В ответе отсутствует поле docs"
    assert isinstance(data["docs"], list), (
        "Поле docs должно содержать список фильмов"
    )
    assert len(data["docs"]) > 0, "Список фильмов пуст"


def test_search_movie_by_title() -> None:
    """KP-API-002: Поиск фильма по названию."""
    assert API_TOKEN, "API_TOKEN не задан в .env"

    response = requests.get(
        f"{BASE_URL}/movie/search",
        headers={
            "X-API-KEY": API_TOKEN,
            "Accept": "application/json",
        },
        params={"query": "Интерстеллар"},
        timeout=15,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers.get(
        "Content-Type", ""
    )

    data = response.json()
    assert "docs" in data

    movies = data["docs"]
    assert isinstance(movies, list)

    assert any(
        movie.get("id") == 258687
        and movie.get("name") == "Интерстеллар"
        for movie in movies
    ), "Фильм «Интерстеллар» не найден"


def test_get_movie_by_id() -> None:
    """KP-API-003: Получение информации о фильме по ID."""
    assert API_TOKEN, "API_TOKEN не задан в .env"

    movie_id = 258687

    response = requests.get(
        f"{BASE_URL}/movie/{movie_id}",
        headers={
            "X-API-KEY": API_TOKEN,
            "Accept": "application/json",
        },
        timeout=15,
    )

    assert response.status_code == 200
    assert "application/json" in response.headers.get(
        "Content-Type", ""
    )

    movie = response.json()

    assert movie["id"] == movie_id
    assert movie["name"] == "Интерстеллар"
    assert movie["year"] == 2014
    assert "genres" in movie
    assert "rating" in movie


def test_get_movie_with_invalid_id() -> None:
    """KP-API-004: Получение фильма по некорректному ID."""
    assert API_TOKEN, "API_TOKEN не задан в .env"

    invalid_movie_id = 999999999

    response = requests.get(
        f"{BASE_URL}/movie/{invalid_movie_id}",
        headers={
            "X-API-KEY": API_TOKEN,
            "Accept": "application/json",
        },
        timeout=15,
    )

    assert response.status_code == 400, (
        f"Ожидался статус 400, получен {response.status_code}"
    )

    data = response.json()

    assert data["statusCode"] == 400
    assert data["error"] == "Bad Request"
    assert "message" in data


def test_get_movie_with_string_id() -> None:
    """KP-API-005: Получение фильма с буквенным ID."""
    assert API_TOKEN, "API_TOKEN не задан в .env"

    response = requests.get(
        f"{BASE_URL}/movie/abc",
        headers={
            "X-API-KEY": API_TOKEN,
            "Accept": "application/json",
        },
        timeout=15,
    )

    assert response.status_code == 400, (
        f"Ожидался статус 400, получен {response.status_code}"
    )

    data = response.json()

    assert data["statusCode"] == 400
    assert data["error"] == "Bad Request"
    assert "message" in data
