from tortoise import fields, models


# --- Администратор ---
class Admin(models.Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=255, unique=True)
    token = fields.CharField(max_length=255, unique=True)

    class Meta:
        table = "admins"
        app_label = "models"


# --- Жанры ---
class Genre(models.Model):
    row_id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "genres"
        app_label = "models"


# --- Ключевые слова ---
class Keyword(models.Model):
    row_id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    name = fields.CharField(max_length=255)

    class Meta:
        table = "keywords"
        app_label = "models"


# --- Люди ---
class Person(models.Model):
    row_id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    name = fields.CharField(max_length=255)
    gender = fields.IntField(null=True)
    profile_path = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "people"
        app_label = "models"


# --- Производственные компании ---
class ProductionCompany(models.Model):
    row_id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    name = fields.CharField(max_length=255)
    origin_country = fields.CharField(max_length=50, null=True)

    class Meta:
        table = "production_companies"
        app_label = "models"


# --- Фильмы ---
class Movie(models.Model):
    row_id = fields.IntField(pk=True)
    tmdb_id = fields.IntField(unique=True)
    adult = fields.BooleanField(null=True)
    backdrop_path = fields.CharField(max_length=255, null=True)
    budget = fields.IntField(null=True)
    homepage = fields.CharField(max_length=255, null=True)
    imdb_id = fields.CharField(max_length=255, null=True)
    original_language = fields.CharField(max_length=50, null=True)
    original_title = fields.CharField(max_length=255, null=True)
    overview = fields.TextField(null=True)
    popularity = fields.FloatField(null=True)
    poster_path = fields.CharField(max_length=255, null=True)
    release_date = fields.CharField(max_length=50, null=True)
    revenue = fields.IntField(null=True)
    runtime = fields.IntField(null=True)
    status = fields.CharField(max_length=50, null=True)
    tagline = fields.CharField(max_length=255, null=True)
    title = fields.TextField(null=True)
    video = fields.BooleanField(null=True)
    vote_average = fields.FloatField(null=True)
    vote_count = fields.IntField(null=True)

    # Отношения многие‑ко‑многим через промежуточные модели:
    genres: fields.ManyToManyRelation[Genre] = fields.ManyToManyField("models.Genre", related_name="movies",
                                                                      through="movie_genres", forward_key="movie_id",
                                                                      backward_key="genre_id")
    keywords: fields.ManyToManyRelation[Keyword] = fields.ManyToManyField("models.Keyword", related_name="movies",
                                                                          through="movie_keywords",
                                                                          forward_key="movie_id",
                                                                          backward_key="keyword_id")

    class Meta:
        table = "movies"
        app_label = "models"


# --- Каст фильма ---
class MovieCast(models.Model):
    row_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="movie_cast", to_field="row_id")
    person = fields.ForeignKeyField("models.Person", related_name="movie_cast", to_field="row_id")
    character = fields.TextField(null=True)
    credit_id = fields.TextField(null=True)
    # Поле "order" в БД, поэтому задаём column_name явно
    order = fields.IntField(null=True, column_name="order")

    class Meta:
        table = "movie_cast"
        app_label = "models"


# --- Съёмочная группа фильма ---
class MovieCrew(models.Model):
    row_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="movie_crew", to_field="row_id")
    person = fields.ForeignKeyField("models.Person", related_name="movie_crew", to_field="row_id")
    job = fields.TextField(null=True)
    department = fields.TextField(null=True)
    credit_id = fields.TextField(null=True)

    class Meta:
        table = "movie_crew"
        app_label = "models"


# --- Компании‑продюсеры фильма ---
class MovieCompany(models.Model):
    row_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="movie_companies", to_field="row_id")
    company = fields.ForeignKeyField("models.ProductionCompany", related_name="movie_companies", to_field="row_id")

    class Meta:
        table = "movie_companies"
        app_label = "models"


# --- Промежуточная таблица для жанров фильма ---
class MovieGenre(models.Model):
    row_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="movie_genres", to_field="row_id")
    genre = fields.ForeignKeyField("models.Genre", related_name="genre_movies", to_field="row_id")

    class Meta:
        table = "movie_genres"
        app_label = "models"


# --- Промежуточная таблица для ключевых слов фильма ---
class MovieKeyword(models.Model):
    row_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField("models.Movie", related_name="movie_keywords", to_field="row_id")
    keyword = fields.ForeignKeyField("models.Keyword", related_name="keyword_movies", to_field="row_id")

    class Meta:
        table = "movie_keywords"
        app_label = "models"


class User(models.Model):
    row_id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    username = fields.CharField(max_length=255)
    password_hash = fields.CharField(max_length=255)
    genres = fields.TextField(null=True)

    class Meta:
        table = "users"
        app_label = "models"
