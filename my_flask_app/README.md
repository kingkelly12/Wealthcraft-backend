# Adulting Flask Backend

Scalable Python/Flask backend with 20 SQLAlchemy models, service layer, and RESTful API.

## Quick Start

```bash
cd my_flask_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate
flask db upgrade

# Run development server
flask run
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user

### Profile Management
- `GET /api/profile/<user_id>` - Get profile
- `POST /api/profile/` - Create profile
- `PUT /api/profile/<user_id>` - Update profile

### Asset Marketplace
- `GET /api/assets/marketplace` - List all assets
- `GET /api/assets/marketplace?category=stocks` - Filter by category
- `GET /api/assets/user/<user_id>` - Get user's portfolio
- `POST /api/assets/buy/<user_id>` - Purchase asset
- `DELETE /api/assets/sell/<user_id>/<asset_id>` - Sell asset

## Models (20 Total)

**Core**: User, Profile, UserBalance, Transaction, Notification  
**Assets**: Asset, UserAsset, Job, Course  
**Liabilities**: Liability, LiabilityItem, P2PLoan, BankLoan  
**Housing**: RentalProperty, PlayerRental  
**Social**: UserFollow, ChatMessage, LifeEvent  
**Missions**: IntegratedMission, PlayerMissionProgress

## Testing

```bash
export PYTHONPATH=$PYTHONPATH:.
pytest -v
```

## Production Deployment

```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```

## Architecture

```
Routes (API) → Services (Logic) → Models (Data) → Database
```

Each layer is independent and testable.
