import logging

from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from core.config import DATABASE_URL
from routes import (
    admin,
    genres,
    keywords,
    people,
    production_companies,
    movies,
    user
)

app = FastAPI(title="Full Movie Database API")

# Роутеры
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(genres.router, prefix="/genres", tags=["Genres"])
app.include_router(keywords.router, prefix="/keywords", tags=["Keywords"])
app.include_router(people.router, prefix="/people", tags=["People"])
app.include_router(production_companies.router, prefix="/company", tags=["Companies"])
app.include_router(movies.router, prefix="/movies", tags=["Movies"])
app.include_router(user.router, prefix="/user", tags=["User"])

register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

logger = logging.getLogger("tortoise")
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
