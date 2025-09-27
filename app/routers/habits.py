# app/routers/habits.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session 

from .. import crud, schemas
from ..database import get_db
from ..dependencies import ActiveUser

router = APIRouter(
    prefix="/habits",
    tags=["العادات (Habits)"],
    responses={404: {"description": "العادة غير موجودة"}}
)

@router.post("/", response_model=schemas.HabitRead, status_code=status.HTTP_201_CREATED)
def create_habit(
    habit: schemas.HabitCreate, 
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser),
):
    """إنشاء عادة جديدة للمستخدم الحالي"""
    return crud.create_user_habit(db=db, habit=habit, user_id=current_user.id)

@router.get("/", response_model=List[schemas.HabitRead])
def read_habits(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser),
):
    """جلب جميع عادات المستخدم الحالي"""
    habits = crud.get_habits(db, user_id=current_user.id, skip=skip, limit=limit)
    return habits

@router.put("/{habit_id}", response_model=schemas.HabitRead)
def update_habit_route(
    habit_id: int, 
    habit: schemas.HabitUpdate, 
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser),
):
    """تعديل عادة معينة للمستخدم الحالي"""
    db_habit = crud.update_habit(db, habit_id=habit_id, user_id=current_user.id, habit_in=habit)
    if db_habit is None:
        raise HTTPException(status_code=404, detail="العادة غير موجودة")
    return db_habit

@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit_route(
    habit_id: int, 
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser),
):
    """حذف عادة معينة للمستخدم الحالي"""
    if not crud.delete_habit(db, habit_id=habit_id, user_id=current_user.id):
        raise HTTPException(status_code=404, detail="العادة غير موجودة")
    return