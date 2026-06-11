from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    products = relationship("Product", back_populates="category")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")
    loyalty_points = Column(Integer, default=0)
    
    # العلاقات المضافة للتقييمات والمنتجات والطلبات
    reviews = relationship("Review", back_populates="user")
    products = relationship("Product", back_populates="owner")
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    stock_quantity = Column(Integer)
    is_deleted = Column(Boolean, default=False)
    
    category_id = Column(Integer, ForeignKey("categories.id"))
    vendor_id = Column(Integer, ForeignKey("users.id"))
    
    # العلاقات المضافة للتقييم والمالك والتصنيف
    category = relationship("Category", back_populates="products")
    owner = relationship("User", back_populates="products")
    reviews = relationship("Review", back_populates="product")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    rating = Column(Integer)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_price = Column(Float)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = relationship("OrderItem", back_populates="order")
    user = relationship("User", back_populates="orders")
    history = relationship("OrderStatusHistory", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    price_at_purchase = Column(Float)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    old_status = Column(String, nullable=True)
    new_status = Column(String)
    changed_by = Column(Integer, ForeignKey("users.id"))
    role = Column(String)
    note = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    order = relationship("Order", back_populates="history")

class Bundle(Base):
    __tablename__ = "bundles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    discount_percentage = Column(Float, default=10.0)

class InventoryLog(Base):
    __tablename__ = "inventory_logs"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    change_amount = Column(Integer)
    reason = Column(String)