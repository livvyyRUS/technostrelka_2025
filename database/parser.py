import asyncio

import aiohttp
from config import tmdb_key
from models import (
    Genre, Keyword, Person, ProductionCompany, Movie,
    MovieCast, MovieCrew, MovieCompany, MovieGenre, MovieKeyword  # Добавлены промежуточные модели
)
from tortoise import Tortoise

API_KEY = tmdb_key  # замените на ваш ключ
BASE_URL = "https://api.themoviedb.org/3"
LANGUAGE = "ru-RU"


async def fetch_json(session: aiohttp.ClientSession, url: str, params: dict = None):
    async with session.get(url, params=params) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f"Ошибка запроса {url} с параметрами {params}: {response.status}")
            return None


async def fetch_popular_movie_ids(session: aiohttp.ClientSession, limit: int = 10000):
    """
    Собирает ID популярных фильмов через /movie/popular с пагинацией.
    """
    movie_ids = []
    page = 1
    while len(movie_ids) < limit:
        url = f"{BASE_URL}/movie/popular"
        params = {"api_key": API_KEY, "language": LANGUAGE, "page": page}
        data = await fetch_json(session, url, params)
        if not data:
            break

        results = data.get("results", [])
        if not results:
            break

        for movie in results:
            movie_ids.append(movie["id"])
            if len(movie_ids) >= limit:
                break

        total_pages = data.get("total_pages", page)
        if page >= total_pages:
            break
        page += 1

    return list(set(movie_ids))  # удаляем дубликаты


async def fetch_and_store_movie(session: aiohttp.ClientSession, movie_id: int):
    """
    Получает детальную информацию о фильме (с кредитами и ключевыми словами)
    и сохраняет данные в базу по модели.
    """
    url = f"{BASE_URL}/movie/{movie_id}"
    params = {"api_key": API_KEY, "language": LANGUAGE, "append_to_response": "credits,keywords"}
    data = await fetch_json(session, url, params)
    if not data:
        return
    # print(data)

    # Сохранение основного объекта фильма
    movie_defaults = {
        "adult": data.get("adult"),
        "backdrop_path": data.get("backdrop_path"),
        "budget": data.get("budget"),
        "homepage": data.get("homepage"),
        "imdb_id": data.get("imdb_id"),
        "original_language": data.get("original_language"),
        "original_title": data.get("original_title"),
        "overview": data.get("overview"),
        "popularity": data.get("popularity"),
        "poster_path": data.get("poster_path"),
        "release_date": data.get("release_date"),
        "revenue": data.get("revenue"),
        "runtime": data.get("runtime"),
        "status": data.get("status"),
        "tagline": data.get("tagline"),
        "title": data.get("title"),
        "video": data.get("video"),
        "vote_average": data.get("vote_average"),
        "vote_count": data.get("vote_count"),
    }
    movie, _ = await Movie.get_or_create(tmdb_id=data["id"], defaults=movie_defaults)
    # Явно убеждаемся, что фильм сохранён и имеет PK
    if not movie.row_id:
        await movie.save()

    # Обработка жанров (связь many‑to‑many через промежуточную таблицу)
    for genre in data.get("genres", []):
        genre_obj, _ = await Genre.get_or_create(
            tmdb_id=genre["id"],
            defaults={"name": genre["name"]}
        )
        # Создаем связь через промежуточную модель MovieGenre
        await MovieGenre.get_or_create(movie=movie, genre=genre_obj)

    # Обработка продакшн-компаний
    for company in data.get("production_companies", []):
        company_obj, _ = await ProductionCompany.get_or_create(
            tmdb_id=company["id"],
            defaults={
                "name": company.get("name"),
                "origin_country": company.get("origin_country")
            }
        )
        if not company_obj.row_id:
            await company_obj.save()
        await MovieCompany.get_or_create(movie=movie, company=company_obj)

    # Обработка ключевых слов
    keywords_data = data.get("keywords", {}).get("keywords", [])
    for keyword in keywords_data:
        keyword_obj, _ = await Keyword.get_or_create(
            tmdb_id=keyword["id"],
            defaults={"name": keyword["name"]}
        )
        # Создаем связь через промежуточную модель MovieKeyword
        await MovieKeyword.get_or_create(movie=movie, keyword=keyword_obj)

    # Обработка кастинга (актеры)
    credits = data.get("credits", {})
    for cast_member in credits.get("cast", []):
        person_obj, _ = await Person.get_or_create(
            tmdb_id=cast_member["id"],
            defaults={
                "name": cast_member.get("name"),
                "gender": cast_member.get("gender"),
                "profile_path": cast_member.get("profile_path")
            }
        )
        if not person_obj.row_id:
            await person_obj.save()
        await MovieCast.get_or_create(
            movie=movie,
            person=person_obj,
            defaults={
                "character": cast_member.get("character"),
                "credit_id": cast_member.get("credit_id"),
                "order": cast_member.get("order")
            }
        )

    # Обработка съёмочной группы
    for crew_member in credits.get("crew", []):
        person_obj, _ = await Person.get_or_create(
            tmdb_id=crew_member["id"],
            defaults={
                "name": crew_member.get("name"),
                "gender": crew_member.get("gender"),
                "profile_path": crew_member.get("profile_path")
            }
        )
        if not person_obj.row_id:
            await person_obj.save()
        await MovieCrew.get_or_create(
            movie=movie,
            person=person_obj,
            defaults={
                "job": crew_member.get("job"),
                "department": crew_member.get("department"),
                "credit_id": crew_member.get("credit_id")
            }
        )


async def main():
    # Инициализируем Tortoise ORM; убедитесь, что база пуста или проведены миграции
    await Tortoise.init(db_url="sqlite://data/tmdb_database_new_all.db", modules={"models": ["models"]})
    await Tortoise.generate_schemas()

    async with aiohttp.ClientSession() as session:
        print("Сбор ID популярных фильмов...")
        movie_ids = await fetch_popular_movie_ids(session, limit=10000)

        movie_ids = set(movie_ids)
        print(f"Собрано {len(movie_ids)} ID фильмов.")
        total = len(movie_ids)
        for idx, movie_id in enumerate(movie_ids, start=1):
            print(f"Обработка фильма {idx}/{total}: TMDB ID {movie_id}")
            movie = await Movie.get_or_none(tmdb_id=movie_id)
            if movie:
                continue
            await fetch_and_store_movie(session, movie_id)

    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())
