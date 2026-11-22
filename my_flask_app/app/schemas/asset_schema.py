from pydantic import BaseModel, Field

class AssetPurchase(BaseModel):
    asset_id: str
    quantity: float = Field(default=1, gt=0)
