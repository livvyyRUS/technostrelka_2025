import secrets

from fastapi import APIRouter

from models import User
from schemas import UserValidate, UserGenresIn, UserRegister
from storage import storage

router = APIRouter()


@router.post('/auth')
async def auth(_data: UserValidate):
    print(_data)
    user = await User.get(email=_data.email, password_hash=_data.password_hash)
    token = secrets.token_hex(32)
    if user:
        storage[token] = user.row_id
        return {"status": "ok", "token": token}
    else:
        return {"status": "bad"}


@router.post('/register')
async def register(_data: UserRegister):
    print(_data)
    user = await User.get_or_none(email=_data.email)
    if user:
        return {"status": "bad", "error": "User already exists"}
    await User.create(username=_data.username, email=_data.email, password_hash=_data.password_hash)
    return {"status": "ok"}


@router.get('/user')
async def get_user(token: str):
    user_id = storage.get(token)
    if user_id is None:
        return {"status": "bad"}

    user = await User.get(row_id=user_id)
    if not user:
        return {"status": "bad"}

    return {
        "status": "ok",
        "id": user.row_id,
        "email": user.email,
        "username": user.username,
        "genres": user.genres.split(",") if user.genres else [],
    }


@router.post("/genres")
async def set_genres(genre_obj: UserGenresIn):
    user_id = storage.get(genre_obj.token)
    if user_id is None:
        return {"status": "bad"}

    user = await User.get(row_id=user_id)
    if not user:
        return {"status": "bad"}

    user.genres = genre_obj.genres
    await user.save()
    return {"status": "ok", "genres": user.genres}


@router.post("close")
async def close(token: str):
    data = storage.pop(token)
    if data:
        return {"status": "ok"}
    else:
        return {"status": "bad"}
