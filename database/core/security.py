import secrets

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

from models import Admin  # импортируем Admin; следите за порядком импорта при инициализации Tortoise

api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=True)


def generate_token() -> str:
    """Генерирует случайный токен для администратора."""
    return secrets.token_hex(16)


async def get_current_admin(api_key: str = Security(api_key_header)) -> Admin:
    admin = await Admin.get_or_none(token=api_key)
    if not admin:
        raise HTTPException(status_code=403, detail="Неверный или отсутствует админский токен")
    return admin
