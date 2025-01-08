from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MenuItem(BaseModel):
    name: str
    price: float
    description: str
    category: str

class Store(BaseModel):
    id: str
    name: str
    owner_id: str
    items: List[MenuItem]
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    share_url: str

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OrderItem(BaseModel):
    menu_item_name: str
    quantity: int
    price: float
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    store_id: str
    items: List[OrderItem]
    buyer_name: str
    contact_info: str  # Could be email or phone
    notes: Optional[str] = None

class Order(BaseModel):
    id: str
    store_id: str
    items: List[OrderItem]
    buyer_name: str
    contact_info: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    notes: Optional[str] = None
