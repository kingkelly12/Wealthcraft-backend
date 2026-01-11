from app import db
from app.models.user import User
from app.schemas.user_schema import UserCreate

class UserService:
    @staticmethod
    def create_user(data: UserCreate) -> User:
        if User.query.filter_by(username=data.username).first():
            raise ValueError("Username already exists")
        if User.query.filter_by(email=data.email).first():
            raise ValueError("Email already exists")

        new_user = User(username=data.username, email=data.email)
        new_user.set_password(data.password)
        
        db.session.add(new_user)
        db.session.commit()
        return new_user

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        return User.query.get(user_id)
