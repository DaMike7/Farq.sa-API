from pydantic import BaseModel
from typing import Optional

class RestaurantBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantResponse(RestaurantBase):
    id: int
    distance_meters: Optional[float] = None

    class Config:
        from_attributes = True

class NearbyQuery(BaseModel):
    latitude: float
    longitude: float
    radius_meters: Optional[int] = 5000
    limit: Optional[int] = 20