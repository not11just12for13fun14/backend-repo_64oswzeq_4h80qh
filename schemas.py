"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List, Literal

# Core user (example left for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

# GenZyFits product schema
class Product(BaseModel):
    title: str = Field(..., description="Product title")
    slug: str = Field(..., description="URL-friendly unique identifier")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in USD")
    category: Literal['Streetwear','Casual','Essentials'] = Field(..., description="Category")
    images: List[HttpUrl] = Field(default_factory=list, description="Image URLs")
    sizes: List[Literal['XS','S','M','L','XL']] = Field(default_factory=list, description="Available sizes")
    tags: List[str] = Field(default_factory=list, description="Tags like 'best','new','seasonal'")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating")
    rating_count: int = Field(0, ge=0, description="Number of ratings")
    in_stock: bool = Field(True, description="Whether product is in stock")

class Review(BaseModel):
    product_id: str = Field(..., description="Related product document _id as string")
    user_name: str = Field(..., description="Display name of reviewer")
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class OrderItem(BaseModel):
    product_id: str
    size: Optional[Literal['XS','S','M','L','XL']] = None
    quantity: int = Field(1, ge=1)
    unit_price: float = Field(..., ge=0)

class Order(BaseModel):
    email: str
    items: List[OrderItem]
    total: float = Field(..., ge=0)
    status: Literal['created','paid','shipped','cancelled'] = 'created'

class Collection(BaseModel):
    key: Literal['best','new','seasonal']
    title: str
    description: Optional[str] = None
    product_ids: List[str] = Field(default_factory=list)

# Size guide entry
class SizeGuide(BaseModel):
    category: Literal['Streetwear','Casual','Essentials']
    rows: List[dict] = Field(..., description="List of size rows with measurements")
