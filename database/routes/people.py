from fastapi import APIRouter, HTTPException, Depends
from tortoise.expressions import Q
from pydantic import BaseModel
from typing import List, Optional

from core.security import get_current_admin
from models import Person
from schemas import PersonIn, PersonOut

router = APIRouter()


class RoleOut(BaseModel):
    role_type: str  # 'cast' или 'crew'
    character: Optional[str] = None  # только для касты
    job: Optional[str] = None  # только для съёмочной группы
    department: Optional[str] = None  # для съёмочной группы


class PersonWithRolesOut(PersonOut):
    roles: List[RoleOut]


@router.get("/", response_model=list[PersonOut])
async def get_people():
    return await Person.all()


@router.get("/people/{person_id}", response_model=PersonOut)
async def get_person(person_id: int):
    person = await Person.get_or_none(row_id=person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person


@router.get("/movie/{movie_id}", response_model=list[PersonWithRolesOut])
async def get_people_by_movie(movie_id: int):
    # Загружаем людей, которые встречаются в касте или съёмочной группе для данного фильма
    people = await Person.filter(
        Q(movie_cast__movie_id=movie_id) | Q(movie_crew__movie_id=movie_id)
    ).distinct().prefetch_related("movie_cast", "movie_crew").all()
    if not people:
        raise HTTPException(status_code=404, detail="No people found for the given movie_id")

    response = []
    for person in people:
        roles = []
        # Обрабатываем записи из касты
        for cast in person.movie_cast:
            # Проверяем, что запись относится к нужному фильму
            if cast.movie_id == movie_id or (hasattr(cast.movie, "row_id") and cast.movie.row_id == movie_id):
                roles.append({
                    "role_type": "cast",
                    "character": cast.character
                })
        # Обрабатываем записи из съёмочной группы
        for crew in person.movie_crew:
            if crew.movie_id == movie_id or (hasattr(crew.movie, "row_id") and crew.movie.row_id == movie_id):
                roles.append({
                    "role_type": "crew",
                    "job": crew.job,
                    "department": crew.department
                })
        person_data = PersonOut.from_orm(person)
        person_dict = person_data.dict()
        person_dict["roles"] = roles
        response.append(person_dict)
    return response


@router.post("/", response_model=PersonOut, dependencies=[Depends(get_current_admin)])
async def create_person(person_in: PersonIn):
    existing = await Person.get_or_none(tmdb_id=person_in.tmdb_id)
    if existing:
        raise HTTPException(status_code=400, detail="Person already exists")
    person = await Person.create(**person_in.model_dump())
    return person
