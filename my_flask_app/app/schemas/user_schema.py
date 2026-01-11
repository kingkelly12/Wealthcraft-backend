from pydantic import BaseModel, EmailStr, constr

class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=64) # type: ignore
    email: EmailStr
    password: constr(min_length=6) # type: ignore

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: str

    class Config:
        from_attributes = True
