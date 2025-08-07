from pydantic import BaseModel, EmailStr

# --- User Schemas ---

# Schema for user creation (request)
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Schema for reading user data (response)
class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True # Pydantic V2 uses this instead of orm_mode
