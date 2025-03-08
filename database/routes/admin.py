from fastapi import APIRouter, HTTPException, Depends

from core.security import generate_token, get_current_admin
from models import Admin
from schemas import AdminCreate, AdminOut, AdminTokenUpdate

router = APIRouter()


@router.post("/", response_model=AdminOut)
async def create_admin(admin_in: AdminCreate):
    # Проверяем, существует ли администратор с таким именем
    existing = await Admin.get_or_none(username=admin_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Администратор с таким именем уже существует")
    token = generate_token()
    admin = await Admin.create(username=admin_in.username, token=token)
    return admin


@router.get("/me", response_model=AdminOut)
async def get_current_admin_info(current_admin=Depends(get_current_admin)):
    return current_admin


@router.patch("/me/token", response_model=AdminOut)
async def update_admin_token(token_update: AdminTokenUpdate, current_admin=Depends(get_current_admin)):
    # Если новый токен не передан, генерируем новый
    new_token = token_update.new_token if token_update.new_token else generate_token()
    current_admin.token = new_token
    await current_admin.save()
    return current_admin
