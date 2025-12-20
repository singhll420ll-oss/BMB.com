"""
SQLAlchemy models for Bite Me Buddy
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    role = Column(String(20), nullable=False, default="customer")  # customer, team_member, admin
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    assigned_orders = relationship("Order", back_populates="team_member", foreign_keys="Order.assigned_to")
    plans = relationship("TeamMemberPlan", back_populates="team_member", foreign_keys="TeamMemberPlan.team_member_id")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    menu_items = relationship("MenuItem", back_populates="service", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="service", cascade="all, delete-orphan")

class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    service = relationship("Service", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, confirmed, preparing, delivering, delivered, cancelled
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("User", back_populates="orders", foreign_keys=[customer_id])
    service = relationship("Service", back_populates="orders")
    team_member = relationship("User", back_populates="assigned_orders", foreign_keys=[assigned_to])
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_at_time = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    menu_item = relationship("MenuItem", back_populates="order_items")

class TeamMemberPlan(Base):
    __tablename__ = "team_member_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_member_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    team_member = relationship("User", back_populates="plans", foreign_keys=[team_member_id])

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    login_time = Column(DateTime, nullable=False, index=True)
    logout_time = Column(DateTime, nullable=True)
    date = Column(Date, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
