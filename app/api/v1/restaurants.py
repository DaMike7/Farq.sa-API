# app/api/v1/restaurants.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from app.core.dependencies import get_db, get_admin_user
from app.models.user import User
from app.schemas.restaurant import RestaurantResponse
from app.services.geo_service import GeoService
from app.tasks.csv_import import import_csv_to_db 

router = APIRouter()

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )

    # Save file to shared volume
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Properly queue with Celery
        task = import_csv_to_db.delay(file_path)
        
        return {
            "message": "CSV import queued successfully",
            "filename": file.filename,
            "task_id": task.id
        }

    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)  # cleanup on error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process upload: {str(e)}"
        )