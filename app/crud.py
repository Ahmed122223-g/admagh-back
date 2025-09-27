# app/crud.py
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel # <--- تم إضافة هذا السطر لحل مشكلة الاسم
from sqlalchemy import func

from . import models, schemas
from .auth_utils import get_password_hash, verify_password
from app.models import Task

# --- عمليات المستخدم (User CRUD) ---
def get_active_task(db: Session, user_id: int):
    return db.query(Task).filter(Task.owner_id == user_id, Task.is_active == True).first()

def start_task_timer(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task:
        return None

    active_task = get_active_task(db, user_id)
    if active_task and active_task.id != task_id:
        # سيتم التعامل مع هذا الخطأ في الواجهة الأمامية لمنع البدء
        return {"error": "Another task is already running."}
    
    # 2. تحديد المدة المتبقية الجديدة
    if task.status == "COMPLETED":
        # لا يمكن بدء مهمة مكتملة
        return {"error": "لا يمكن بدء مهمة مكتملة."}
    if task.status == "INCOMPLETE":
        # كل مرة تبدأ مهمة غير مكتملة تبدأ من ساعة واحدة فقط
        new_remaining_time = 3600
    elif task.status == "TO_DO" or task.remaining_time_seconds <= 0:
        # بدء مهمة جديدة: استخدام المدة الأصلية
        new_remaining_time = task.initial_duration_seconds
    else:
        # استئناف مهمة قيد التقدم تم إيقافها مؤقتاً
        new_remaining_time = task.remaining_time_seconds
        
    # 3. تحديث حالة المهمة
    task.is_active = True
    task.start_time = datetime.utcnow()
    task.status = "IN_PROGRESS"
    task.remaining_time_seconds = new_remaining_time
    task.last_run_date = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    return task

# دالة إيقاف المؤقت وحفظ التقدم (مستخدمة للإيقاف المؤقت أو عند انتهاء الوقت)
def stop_task_timer(db: Session, task_id: int, user_id: int):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task or not task.is_active:
        return None

    # حساب المدة المنقضية وحفظها
    elapsed_time = (datetime.utcnow() - task.start_time).total_seconds()
    task.time_spent_seconds += int(elapsed_time)
    task.remaining_time_seconds = max(0, task.remaining_time_seconds - int(elapsed_time))
    
    # إيقاف الحالة النشطة
    task.is_active = False
    task.start_time = None 
    
    db.commit()
    db.refresh(task)
    return task

# دالة إكمال المهمة (تستخدم بعد stop_task_timer)
def complete_task(db: Session, task_id: int, user_id: int, progress_details: str = None):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task: return None

    task.status = "COMPLETED"
    task.completed = True
    if progress_details is not None:
        task.progress_details = progress_details
    db.commit()
    db.refresh(task)
    return task

# دالة وسم المهمة كغير مكتملة (تستخدم بعد stop_task_timer)
def mark_task_incomplete(db: Session, task_id: int, user_id: int, progress_details: str = None):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task: return None

    task.status = "INCOMPLETE"
    task.completed = False
    # عند إعادة فتح مهمة غير مكتملة، المؤقت سيبدأ من ساعة واحدة فقط (يتم ذلك في start_task_timer)
    if progress_details is not None:
        task.progress_details = progress_details
    db.commit()
    db.refresh(task)
    return task

# دالة تنظيف المهام التي لم تنجز في نهاية اليوم
def end_of_day_cleanup(db: Session):
    # تحديد المهام التي لم يتم إكمالها وتاريخ استحقاقها قد فات
    tasks_to_mark_incomplete = db.query(Task).filter(
        Task.status.in_(["TO_DO", "IN_PROGRESS"]), # المهام التي لم تكتمل بعد
        Task.is_active == False # ليست قيد التشغيل حالياً (تم إيقافها أو لم تبدأ)
    ).all()
    
    for task in tasks_to_mark_incomplete:
        # نستخدم دالة stop_task_timer لإيقاف أي مهمة قد تكون نشطة (للتأكد)
        if task.is_active:
             stop_task_timer(db, task.id, task.owner_id)
             
        task.status = "INCOMPLETE"
        db.add(task)
        
    db.commit()
    return {"message": f"تم نقل {len(tasks_to_mark_incomplete)} مهمة إلى المهام غير المكتملة."}

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def set_user_unlocked(db: Session, user_id: int, unlocked: bool = True) -> Optional[models.User]:
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    db_user.is_unlocked = unlocked
    db.commit()
    db.refresh(db_user)
    return db_user

def update_subscription(db: Session, user_id: int, subscription: schemas.SubscriptionUpdate) -> Optional[models.User]:
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    db_user.plan = subscription.plan
    db_user.subscription_id = subscription.subscription_id
    db_user.expires_at = subscription.expires_at
    db.commit()
    db.refresh(db_user)
    return db_user

# --- وظيفة مساعدة لتحديث أي نموذج ---
# BaseModel هنا يشير إلى أي نموذج Pydantic (مثل TaskUpdate, NoteUpdate, HabitUpdate)
def update_item(db: Session, db_item: models.Base, item_in: BaseModel):
    update_data = item_in.model_dump(exclude_unset=True) 
    for key, value in update_data.items():
        # التأكد من أن الحقل موجود في نموذج قاعدة البيانات قبل التحديث
        if hasattr(db_item, key):
             setattr(db_item, key, value)
        
    db.commit()
    db.refresh(db_item)
    return db_item

# --- عمليات المهام (Task CRUD) ---
def get_tasks(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Task]:
    return db.query(models.Task).filter(models.Task.owner_id == user_id).offset(skip).limit(limit).all()

def get_task(db: Session, task_id: int, user_id: int) -> Optional[models.Task]:
    return db.query(models.Task).filter(models.Task.id == task_id, models.Task.owner_id == user_id).first()

def create_user_task(db: Session, task: schemas.TaskCreate, user_id: int) -> models.Task:
    initial_duration_seconds = int(task.estimated_hours * 3600)
    db_task = models.Task(
        **task.model_dump(), 
        owner_id=user_id,
        initial_duration_seconds=initial_duration_seconds,
        remaining_time_seconds=initial_duration_seconds # Set remaining time to full duration initially
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task(db: Session, task_id: int, user_id: int, task_in: schemas.TaskUpdate) -> Optional[models.Task]:
    db_task = get_task(db, task_id, user_id)
    return update_item(db, db_task, task_in) if db_task else None

def delete_task(db: Session, task_id: int, user_id: int) -> bool:
    db_task = get_task(db, task_id, user_id)
    if db_task:
        db.delete(db_task)
        db.commit()
        return True
    return False

# --- عمليات الملاحظات (Note CRUD) ---
def get_notes(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Note]:
    return db.query(models.Note).filter(models.Note.owner_id == user_id).order_by(models.Note.created_at.desc()).offset(skip).limit(limit).all()

def create_user_note(db: Session, note: schemas.NoteCreate, user_id: int) -> models.Note:
    db_note = models.Note(**note.model_dump(), owner_id=user_id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

def update_note(db: Session, note_id: int, user_id: int, note_in: schemas.NoteUpdate) -> Optional[models.Note]:
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == user_id).first()
    return update_item(db, db_note, note_in) if db_note else None

def delete_note(db: Session, note_id: int, user_id: int) -> bool:
    db_note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == user_id).first()
    if db_note:
        db.delete(db_note)
        db.commit()
        return True
    return False
    
# --- عمليات العادات (Habit CRUD) ---
def get_habits(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.Habit]:
    return db.query(models.Habit).filter(models.Habit.owner_id == user_id).order_by(models.Habit.created_at.desc()).offset(skip).limit(limit).all()

def create_user_habit(db: Session, habit: schemas.HabitCreate, user_id: int) -> models.Habit:
    db_habit = models.Habit(**habit.model_dump(), owner_id=user_id)
    db.add(db_habit)
    db.commit()
    db.refresh(db_habit)
    return db_habit

def update_habit(db: Session, habit_id: int, user_id: int, habit_in: schemas.HabitUpdate) -> Optional[models.Habit]:
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.owner_id == user_id).first()
    return update_item(db, db_habit, habit_in) if db_habit else None

def delete_habit(db: Session, habit_id: int, user_id: int) -> bool:
    db_habit = db.query(models.Habit).filter(models.Habit.id == habit_id, models.Habit.owner_id == user_id).first()
    if db_habit:
        db.delete(db_habit)
        db.commit()
        return True
    return False

# --- عمليات إحصائيات التقارير (Report Statistics) ---

def get_user_report_stats(db: Session, user_id: int) -> schemas.ReportStats:
    # الحصول على تاريخ بداية ونهاية الشهر الحالي
    today = datetime.utcnow()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. إحصائيات المهام الشهرية
    monthly_tasks = db.query(models.Task).filter(
        models.Task.owner_id == user_id,
        models.Task.created_at >= start_of_month
    ).all()
    
    completed_tasks = sum(1 for task in monthly_tasks if task.completed)
    total_tasks = len(monthly_tasks)
    total_hours = sum(task.estimated_hours for task in monthly_tasks)
    
    monthly_stats = schemas.MonthlyStats(
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        total_hours=total_hours
    )
    
    # 2. معدل الإكمال الإجمالي
    total_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # 3. أفضل سلسلة للعادات
    habits = get_habits(db, user_id=user_id)
    best_habit_streak = max((habit.best_streak for habit in habits), default=0)
    
    # 4. إحصائيات الفئات
    category_stats = []
    categories = {task.category for task in monthly_tasks if task.category}
    
    # ألوان افتراضية للفئات
    colors = ["text-blue-500", "text-green-500", "text-red-500", "text-yellow-500", "text-purple-500"]
    
    for i, category_name in enumerate(categories):
        tasks_in_cat = [t for t in monthly_tasks if t.category == category_name]
        completed_in_cat = sum(1 for t in tasks_in_cat if t.completed)
        total_in_cat = len(tasks_in_cat)
        rate = (completed_in_cat / total_in_cat * 100) if total_in_cat > 0 else 0
        
        category_stats.append(schemas.CategoryStat(
            name=category_name,
            color=colors[i % len(colors)], # تعيين لون متكرر
            completed=completed_in_cat,
            total=total_in_cat,
            rate=rate
        ))
        
    return schemas.ReportStats(
        monthly_stats=monthly_stats,
        total_completion_rate=total_completion_rate,
        best_habit_streak=best_habit_streak,
        category_stats=category_stats
    )