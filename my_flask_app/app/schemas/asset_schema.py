from pydantic import BaseModel, Field
from typing import Optional

class AssetPurchase(BaseModel):
    asset_id: str
    quantity: float = Field(default=1, gt=0)

class AssetResponse(BaseModel):
    id: str
    name: str
    category: str
    price: float
    price_change: Optional[float] = None
    monthly_income: Optional[float] = None
    description: Optional[str] = None
    risk_level: str
    availability: int

    class Config:
        from_attributes = True

class UserAssetResponse(BaseModel):
    id: str
    user_id: str
    asset_type: str
    name: str
    value: float
    quantity: float
    purchase_price: Optional[float] = None
    purchase_date: Optional[str] = None

    class Config:
        from_attributes = True
