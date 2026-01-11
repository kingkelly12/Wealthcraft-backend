from app import db
from app.models.user_asset import UserAsset
from app.models.asset import Asset
from app.models.transaction import Transaction
from typing import List, Optional
import uuid
from datetime import datetime

class AssetService:
    @staticmethod
    def get_marketplace_assets(category: Optional[str] = None) -> List[Asset]:
        """Get all marketplace assets, optionally filtered by category"""
        query = Asset.query
        if category:
            query = query.filter_by(category=category)
        return query.all()

    @staticmethod
    def get_user_assets(user_id: uuid.UUID) -> List[UserAsset]:
        """Get all assets owned by a user"""
        return UserAsset.query.filter_by(user_id=user_id).all()

    @staticmethod
    def buy_asset(user_id: uuid.UUID, asset_id: str, quantity: float = 1) -> UserAsset:
        """Purchase an asset from the marketplace"""
        asset = Asset.query.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")

        purchase_price = float(asset.price) * quantity

        # Create user asset record
        user_asset = UserAsset(
            user_id=user_id,
            asset_type=asset.category,
            name=asset.name,
            value=purchase_price,
            quantity=quantity,
            purchase_price=purchase_price
        )
        db.session.add(user_asset)

        # Log transaction
        transaction = Transaction(
            user_id=user_id,
            type='investment',
            category=asset.category,
            amount=purchase_price,
            description=f"Purchased {quantity} {asset.name}"
        )
        db.session.add(transaction)

        db.session.commit()
        return user_asset

    @staticmethod
    def sell_asset(user_asset_id: uuid.UUID, user_id: uuid.UUID) -> float:
        """Sell a user's asset"""
        user_asset = UserAsset.query.filter_by(id=user_asset_id, user_id=user_id).first()
        if not user_asset:
            raise ValueError("Asset not found or does not belong to user")

        sale_value = float(user_asset.value)

        # Log transaction
        transaction = Transaction(
            user_id=user_id,
            type='income',
            category='asset_sale',
            amount=sale_value,
            description=f"Sold {user_asset.name}"
        )
        db.session.add(transaction)

        # Delete the asset
        db.session.delete(user_asset)
        db.session.commit()

        return sale_value

    @staticmethod
    def update_asset_value(user_asset_id: uuid.UUID, new_value: float) -> Optional[UserAsset]:
        """Update the value of a user's asset"""
        user_asset = UserAsset.query.get(user_asset_id)
        if user_asset:
            user_asset.value = new_value
            db.session.commit()
        return user_asset
