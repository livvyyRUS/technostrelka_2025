from fastapi import APIRouter, HTTPException, Depends

from core.security import get_current_admin
from models import Keyword
from schemas import KeywordIn, KeywordOut

router = APIRouter()


@router.get("/", response_model=list[KeywordOut])
async def get_keywords():
    return await Keyword.all()


@router.get("/{keyword_id}", response_model=KeywordOut)
async def get_keyword(keyword_id: int):
    keyword = await Keyword.get_or_none(row_id=keyword_id)
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.post("/", response_model=KeywordOut, dependencies=[Depends(get_current_admin)])
async def create_keyword(keyword_in: KeywordIn):
    existing = await Keyword.get_or_none(tmdb_id=keyword_in.tmdb_id)
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    keyword = await Keyword.create(**keyword_in.model_dump())
    return keyword
