from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# --- 1. User Schemas ---

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "customer"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    class Config: from_attributes = True

# ✅ تم إضافته لحل خطأ AttributeError الموضح في الصورة الأخيرة
class UserEmailSchema(BaseModel):
    email: str
    username: str

# --- 2. Review Schemas (نظام التقييم الجديد) ---

class ReviewCreate(BaseModel):
    product_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    rating: int
    comment: Optional[str]
    user: UserResponse
    created_at: datetime
    class Config: from_attributes = True

# --- 3. Product Schemas ---

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock_quantity: int
    category_id: int

class ProductCreate(ProductBase):
    vendor_id: int

class ProductResponse(ProductBase):
    id: int
    vendor_id: int
    owner: Optional[UserResponse] = None 
    # ✅ الحقل الذي سيعرض النجوم في الماركت بليس
    avg_rating: Optional[float] = 0.0 
    reviews: List[ReviewResponse] = []
    class Config: from_attributes = True

# --- 4. Order Schemas ---

class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: float = 0.0 
    product: Optional[ProductResponse] = None
    class Config: from_attributes = True

class OrderCreate(BaseModel):
    items: List[dict]

class OrderStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None

class OrderStatusHistoryResponse(BaseModel):
    id: int
    old_status: Optional[str]
    new_status: str
    role: str
    changed_at: datetime
    note: Optional[str]
    class Config: from_attributes = True

class OrderResponse(BaseModel):
    id: int
    total_price: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []
    history: List[OrderStatusHistoryResponse] = []
    class Config: from_attributes = True