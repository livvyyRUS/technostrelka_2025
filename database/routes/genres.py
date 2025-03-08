from fastapi import APIRouter, HTTPException, Depends

from core.security import get_current_admin
from models import Genre
from schemas import GenreIn, GenreOut

router = APIRouter()


@router.get("/", response_model=list[GenreOut])
async def get_genres():
    return await Genre.all()


@router.get("/{genre_id}", response_model=GenreOut)
async def get_genre(genre_id: int):
    genre = await Genre.get_or_none(row_id=genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.post("/", response_model=GenreOut, dependencies=[Depends(get_current_admin)])
async def create_genre(genre_in: GenreIn):
    existing = await Genre.get_or_none(tmdb_id=genre_in.tmdb_id)
    if existing:
        raise HTTPException(status_code=400, detail="Genre already exists")
    genre = await Genre.create(**genre_in.model_dump())
    return genre
