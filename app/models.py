# app/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# --- نموذج المستخدم (User) ---
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    # whether the user has unlocked the full app (set after verified payment)
    is_unlocked = Column(Boolean, default=False)
    plan = Column(String, nullable=True)
    subscription_id = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    tasks = relationship("Task", back_populates="owner")
    notes = relationship("Note", back_populates="owner")
    habits = relationship("Habit", back_populates="owner")
    
# --- نموذج المهمة (Task) ---
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    priority = Column(String, default="متوسطة") 
    status = Column(String, default="لم تبدأ") 
    due_date = Column(DateTime)
    category = Column(String, default="عام")
    completed = Column(Boolean, default=False)
    estimated_hours = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)
    start_time = Column(DateTime, nullable=True)
    remaining_time_seconds = Column(Integer, default=0, nullable=False)
    time_spent_seconds = Column(Integer, default=0, nullable=False)
    initial_duration_seconds = Column(Integer, default=3600, nullable=False)
    last_run_date = Column(DateTime, nullable=True)
    progress_details = Column(Text, nullable=True)

    owner = relationship("User", back_populates="tasks")

# --- نموذج الملاحظة (Note) ---
class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(Text)
    category = Column(String, default="أفكار")
    is_starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="notes")

# --- نموذج العادة (Habit) ---
class Habit(Base):
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, index=True)
    category = Column(String, default="شخصي")
    days_of_week = Column(String) 
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_completed = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="habits")