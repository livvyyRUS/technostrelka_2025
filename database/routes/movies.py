from fastapi import APIRouter, HTTPException, Depends, Query
from tortoise.expressions import RawSQL

from core.security import get_current_admin
from models import Movie, Genre, Keyword, MovieGenre, MovieKeyword
from schemas import MovieIn, MovieOut

router = APIRouter()


@router.get("/all_movies", response_model=list[MovieOut])
async def get_all_movies():
    movies = await Movie.all()

    result = []
    for m in movies:
        genres_id = await MovieGenre.filter(movie_id=m.row_id)
        genres = [(await genre.genre.get()).name for genre in genres_id]

        keywords_id = await MovieKeyword.filter(movie_id=m.row_id)
        keywords = [(await keyword.keyword.get()).name for keyword in keywords_id]

        result.append({
            "row_id": m.row_id,
            "tmdb_id": m.tmdb_id,
            "adult": m.adult,
            "backdrop_path": m.backdrop_path,
            "budget": m.budget,
            "homepage": m.homepage,
            "imdb_id": m.imdb_id,
            "original_language": m.original_language,
            "original_title": m.original_title,
            "overview": m.overview,
            "popularity": m.popularity,
            "poster_path": m.poster_path,
            "release_date": m.release_date,
            "revenue": m.revenue,
            "runtime": m.runtime,
            "status": m.status,
            "tagline": m.tagline,
            "title": m.title,
            "video": m.video,
            "vote_average": m.vote_average,
            "vote_count": m.vote_count,
            "genres": genres,
            "keywords": keywords
        })
    return result


@router.get("/")
async def get_movies(movie: list[int] = Query()):
    print("test")
    result = []
    for m in movie:
        movie = await Movie.get_or_none(row_id=m).prefetch_related("genres", "keywords")
        genres_id = await MovieGenre.filter(movie_id=m)
        genres = [(await genre.genre.get()).name for genre in genres_id]

        keywords_id = await MovieKeyword.filter(movie_id=m)
        keywords = [(await keyword.keyword.get()).name for keyword in keywords_id]

        result.append({
            "row_id": movie.row_id,
            "tmdb_id": movie.tmdb_id,
            "adult": movie.adult,
            "backdrop_path": movie.backdrop_path,
            "budget": movie.budget,
            "homepage": movie.homepage,
            "imdb_id": movie.imdb_id,
            "original_language": movie.original_language,
            "original_title": movie.original_title,
            "overview": movie.overview,
            "popularity": movie.popularity,
            "poster_path": movie.poster_path,
            "release_date": movie.release_date,
            "revenue": movie.revenue,
            "runtime": movie.runtime,
            "status": movie.status,
            "tagline": movie.tagline,
            "title": movie.title,
            "video": movie.video,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "genres": genres,
            "keywords": keywords
        })
    return result


@router.get("/all", response_model=list[MovieOut])
async def get_movies(page: int = 1):
    item_per_page = 30

    movies = await Movie.filter().offset((page - 1) * item_per_page).limit(item_per_page)

    result = []
    for m in movies:
        genres_id = await MovieGenre.filter(movie_id=m.row_id)
        genres = [(await genre.genre.get()).name for genre in genres_id]

        keywords_id = await MovieKeyword.filter(movie_id=m.row_id)
        keywords = [(await keyword.keyword.get()).name for keyword in keywords_id]

        result.append({
            "row_id": m.row_id,
            "tmdb_id": m.tmdb_id,
            "adult": m.adult,
            "backdrop_path": m.backdrop_path,
            "budget": m.budget,
            "homepage": m.homepage,
            "imdb_id": m.imdb_id,
            "original_language": m.original_language,
            "original_title": m.original_title,
            "overview": m.overview,
            "popularity": m.popularity,
            "poster_path": m.poster_path,
            "release_date": m.release_date,
            "revenue": m.revenue,
            "runtime": m.runtime,
            "status": m.status,
            "tagline": m.tagline,
            "title": m.title,
            "video": m.video,
            "vote_average": m.vote_average,
            "vote_count": m.vote_count,
            "genres": genres,
            "keywords": keywords
        })
    return result


@router.post("/", response_model=MovieOut, dependencies=[Depends(get_current_admin)])
async def create_movie(movie_in: MovieIn):
    existing = await Movie.get_or_none(tmdb_id=movie_in.tmdb_id)
    if existing:
        raise HTTPException(status_code=400, detail="Movie with this tmdb_id already exists")
    movie = await Movie.create(
        tmdb_id=movie_in.tmdb_id,
        adult=movie_in.adult,
        backdrop_path=movie_in.backdrop_path,
        budget=movie_in.budget,
        homepage=movie_in.homepage,
        imdb_id=movie_in.imdb_id,
        original_language=movie_in.original_language,
        original_title=movie_in.original_title,
        overview=movie_in.overview,
        popularity=movie_in.popularity,
        poster_path=movie_in.poster_path,
        release_date=movie_in.release_date,
        revenue=movie_in.revenue,
        runtime=movie_in.runtime,
        status=movie_in.status,
        tagline=movie_in.tagline,
        title=movie_in.title,
        video=movie_in.video,
        vote_average=movie_in.vote_average,
        vote_count=movie_in.vote_count
    )
    if movie_in.genre_ids:
        genres = await Genre.filter(row_id__in=movie_in.genre_ids)
        await movie.genres.add(*genres)
    if movie_in.keyword_ids:
        keywords = await Keyword.filter(row_id__in=movie_in.keyword_ids)
        await movie.keywords.add(*keywords)
    movie = await Movie.get(row_id=movie.row_id).prefetch_related("genres", "keywords")

    genres_id = await MovieGenre.filter(movie_id=movie.row_id)
    genres = [(await genre.genre.get()).name for genre in genres_id]

    keywords_id = await MovieKeyword.filter(movie_id=movie.row_id)
    keywords = [(await keyword.keyword.get()).name for keyword in keywords_id]

    return {
        "row_id": movie.row_id,
        "tmdb_id": movie.tmdb_id,
        "adult": movie.adult,
        "backdrop_path": movie.backdrop_path,
        "budget": movie.budget,
        "homepage": movie.homepage,
        "imdb_id": movie.imdb_id,
        "original_language": movie.original_language,
        "original_title": movie.original_title,
        "overview": movie.overview,
        "popularity": movie.popularity,
        "poster_path": movie.poster_path,
        "release_date": movie.release_date,
        "revenue": movie.revenue,
        "runtime": movie.runtime,
        "status": movie.status,
        "tagline": movie.tagline,
        "title": movie.title,
        "video": movie.video,
        "vote_average": movie.vote_average,
        "vote_count": movie.vote_count,
        "genres": genres,
        "keywords": keywords
    }


@router.get("/get_by_genres/")
async def get_by_genres(genres: str):
    _genres = [(await Genre.get(name=item)).row_id for item in genres.split(",")]
    print(_genres)
    films_ids = await MovieGenre.filter(genre_id__in=_genres).annotate(
        random=RawSQL("RANDOM()")
    ).order_by("random").limit(12).all()
    result = []
    for film_id in films_ids:
        m = await film_id.movie
        print(film_id.row_id, m)
        genres_id = await MovieGenre.filter(movie_id=m.row_id)
        genres = [(await genre.genre.get()).name for genre in genres_id]

        keywords_id = await MovieKeyword.filter(movie_id=m.row_id)
        keywords = [(await keyword.keyword.get()).name for keyword in keywords_id]

        result.append({
            "row_id": m.row_id,
            "tmdb_id": m.tmdb_id,
            "adult": m.adult,
            "backdrop_path": m.backdrop_path,
            "budget": m.budget,
            "homepage": m.homepage,
            "imdb_id": m.imdb_id,
            "original_language": m.original_language,
            "original_title": m.original_title,
            "overview": m.overview,
            "popularity": m.popularity,
            "poster_path": m.poster_path,
            "release_date": m.release_date,
            "revenue": m.revenue,
            "runtime": m.runtime,
            "status": m.status,
            "tagline": m.tagline,
            "title": m.title,
            "video": m.video,
            "vote_average": m.vote_average,
            "vote_count": m.vote_count,
            "genres": genres,
            "keywords": keywords
        })
    return result
