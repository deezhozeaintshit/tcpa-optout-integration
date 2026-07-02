from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.core.security import verify_api_key
from app.models.integration import Integration
from app.schemas.integration import IntegrationResponse, IntegrationCreate, IntegrationUpdate

# All endpoints in this router require API key authentication
router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.post("/", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    payload: IntegrationCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new downstream CRM, dialer, or webhook integration target."""
    stmt = select(Integration).where(Integration.name == payload.name)
    duplicate = (await db.execute(stmt)).scalars().first()
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An integration with this name already exists."
        )
        
    db_obj = Integration(**payload.model_dump())
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(
    db: AsyncSession = Depends(get_db)
):
    """List all registered downstream integration targets."""
    stmt = select(Integration)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{id}", response_model=IntegrationResponse)
async def get_integration(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details for a specific integration config."""
    stmt = select(Integration).where(Integration.id == id)
    db_obj = (await db.execute(stmt)).scalars().first()
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration target not found.")
    return db_obj

@router.patch("/{id}", response_model=IntegrationResponse)
async def update_integration(
    id: int,
    payload: IntegrationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Modify parameters or update credentials/tokens for an existing integration target."""
    stmt = select(Integration).where(Integration.id == id)
    db_obj = (await db.execute(stmt)).scalars().first()
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration target not found.")
        
    data = payload.model_dump(exclude_unset=True)
    for field, val in data.items():
        setattr(db_obj, field, val)
        
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a downstream integration target. Staged tasks remain but won't be dispatched."""
    stmt = select(Integration).where(Integration.id == id)
    db_obj = (await db.execute(stmt)).scalars().first()
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration target not found.")
        
    await db.delete(db_obj)
    await db.commit()
    return None
