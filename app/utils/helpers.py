import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

def validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= latitude <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90"
        )
    if not (-180 <= longitude <= 180):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180"
        )

def create_geo_key(latitude: float, longitude: float, radius_meters: int, limit: int) -> str:
    lat = round(latitude, 4)
    lng = round(longitude, 4)
    return f"nearby:{lat}:{lng}:{radius_meters}:{limit}"