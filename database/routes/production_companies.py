from fastapi import APIRouter, HTTPException, Depends

from core.security import get_current_admin
from models import ProductionCompany
from schemas import ProductionCompanyIn, ProductionCompanyOut

router = APIRouter()


@router.get("/", response_model=list[ProductionCompanyOut])
async def get_companies():
    return await ProductionCompany.all()


@router.get("/movie/{movie_id}", response_model=list[ProductionCompanyOut])
async def get_companies_by_movie(movie_id: int):
    companies = await ProductionCompany.filter(movie_companies__movie_id=movie_id).all()
    if not companies:
        raise HTTPException(status_code=404, detail="No production companies found for the given movie_id")
    return companies


@router.get("/company/{company_id}", response_model=ProductionCompanyOut)
async def get_company(company_id: int):
    company = await ProductionCompany.get_or_none(row_id=company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.post("/", response_model=ProductionCompanyOut, dependencies=[Depends(get_current_admin)])
async def create_company(company_in: ProductionCompanyIn):
    existing = await ProductionCompany.get_or_none(tmdb_id=company_in.tmdb_id)
    if existing:
        raise HTTPException(status_code=400, detail="Company already exists")
    company = await ProductionCompany.create(**company_in.model_dump())
    return company
