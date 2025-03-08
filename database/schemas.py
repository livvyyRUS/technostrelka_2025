from typing import List, Optional

from pydantic import BaseModel


# --- Схемы для администратора ---
class AdminCreate(BaseModel):
    username: str


class AdminOut(BaseModel):
    id: int
    username: str
    token: str

    class Config:
        from_attributes = True


class AdminTokenUpdate(BaseModel):
    # Если значение не передано, сгенерируется новый токен
    new_token: Optional[str] = None


# --- Жанры ---
class GenreIn(BaseModel):
    tmdb_id: int
    name: str


class GenreOut(GenreIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Ключевые слова ---
class KeywordIn(BaseModel):
    tmdb_id: int
    name: str


class KeywordOut(KeywordIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Люди ---
class PersonIn(BaseModel):
    tmdb_id: int
    name: str
    gender: Optional[int] = None
    profile_path: Optional[str] = None


class PersonOut(PersonIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Производственные компании ---
class ProductionCompanyIn(BaseModel):
    tmdb_id: int
    name: str
    origin_country: Optional[str] = None


class ProductionCompanyOut(ProductionCompanyIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Фильмы ---
class MovieIn(BaseModel):
    tmdb_id: int
    adult: Optional[bool] = None
    backdrop_path: Optional[str] = None
    budget: Optional[int] = None
    homepage: Optional[str] = None
    imdb_id: Optional[str] = None
    original_language: Optional[str] = None
    original_title: Optional[str] = None
    overview: Optional[str] = None
    popularity: Optional[float] = None
    poster_path: Optional[str] = None
    release_date: Optional[str] = None
    revenue: Optional[int] = None
    runtime: Optional[int] = None
    status: Optional[str] = None
    tagline: Optional[str] = None
    title: str
    video: Optional[bool] = None
    vote_average: Optional[float] = None
    vote_count: Optional[int] = None
    genre_ids: Optional[List[int]] = []
    keyword_ids: Optional[List[int]] = []


class MovieOut(BaseModel):
    row_id: int
    tmdb_id: int
    adult: Optional[bool]
    backdrop_path: Optional[str]
    budget: Optional[int]
    homepage: Optional[str]
    imdb_id: Optional[str]
    original_language: Optional[str]
    original_title: Optional[str]
    overview: Optional[str]
    popularity: Optional[float]
    poster_path: Optional[str]
    release_date: Optional[str]
    revenue: Optional[int]
    runtime: Optional[int]
    status: Optional[str]
    tagline: Optional[str]
    title: str
    video: Optional[bool]
    vote_average: Optional[float]
    vote_count: Optional[int]
    genres: List[str] = []
    keywords: List[str] = []

    class Config:
        from_attributes = True


# --- Каст фильма ---
class MovieCastIn(BaseModel):
    movie_id: int
    person_id: int
    character: Optional[str] = None
    credit_id: str
    order: Optional[int] = None


class MovieCastOut(MovieCastIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Съёмочная группа фильма ---
class MovieCrewIn(BaseModel):
    movie_id: int
    person_id: int
    job: Optional[str] = None
    department: Optional[str] = None
    credit_id: str


class MovieCrewOut(MovieCrewIn):
    row_id: int

    class Config:
        from_attributes = True


# --- Компании‑продюсеры фильма ---
class MovieCompanyIn(BaseModel):
    movie_id: int
    company_id: int


class MovieCompanyOut(MovieCompanyIn):
    row_id: int

    class Config:
        from_attributes = True


class UserRegister(BaseModel):
    username: str
    email: str
    password_hash: str


class UserValidate(BaseModel):
    email: str
    password_hash: str


class UserGenresIn(BaseModel):
    token: str
    genres: str
