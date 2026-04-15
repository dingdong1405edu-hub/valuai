"""Company CRUD endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Company
from app.models.schemas import APIResponse, CompanyCreate, CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])
logger = logging.getLogger(__name__)


@router.post("", response_model=APIResponse[CompanyOut])
async def create_company(
    payload: CompanyCreate,
    db: AsyncSession = Depends(get_db),
):
    logger.info(f"[COMPANIES] create — name={payload.name}")
    company = Company(
        name=payload.name,
        industry=payload.industry,
        founded_year=payload.founded_year,
        employee_count=payload.employee_count,
        description=payload.description,
        metadata_=payload.metadata,
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    logger.info(f"[COMPANIES] created id={company.id}")
    return APIResponse.ok(CompanyOut.model_validate(company))


@router.get("/{company_id}", response_model=APIResponse[CompanyOut])
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return APIResponse.ok(CompanyOut.model_validate(company))


@router.get("", response_model=APIResponse[List[CompanyOut]])
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company).order_by(Company.created_at.desc()).limit(50))
    companies = result.scalars().all()
    return APIResponse.ok([CompanyOut.model_validate(c) for c in companies])


@router.delete("/{company_id}", response_model=APIResponse[dict])
async def delete_company(company_id: str, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    await db.delete(company)
    await db.commit()
    return APIResponse.ok({"deleted": company_id})
