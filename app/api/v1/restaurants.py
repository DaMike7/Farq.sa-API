# app/api/v1/restaurants.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.dependencies import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.schemas.restaurant import NearbyQuery, RestaurantResponse
from app.services.geo_service import GeoService
from app.tasks.csv_import import import_csv_to_db
import os
import tempfile

router = APIRouter()

@router.get("/nearby", response_model=List[RestaurantResponse])
async def get_nearby_restaurants(
    latitude: float = Query(..., description="User latitude"),
    longitude: float = Query(..., description="User longitude"),
    radius_meters: int = Query(5000, ge=1000, le=50000),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    geo_service = GeoService(db)
    restaurants = await geo_service.get_nearby(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit
    )
    if not restaurants:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No restaurants found in the specified area"
        )
    return restaurants

@router.post("/import", status_code=status.HTTP_202_ACCEPTED)
async def import_restaurants_csv(
    file: UploadFile = File(..., description="CSV file with restaurant data"),
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_file:
            contents = await file.read()
            tmp_file.write(contents)
            tmp_path = tmp_file.name
        
        # Fire and forget - run in background (no Celery needed for now)
        # In production, replace with Celery task
        import os
        from asyncio import create_task
        create_task(import_csv_to_db(tmp_path))
        
        return {"message": "CSV import started successfully", "filename": file.filename}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)