# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional

# --- نماذج المصادقة (Auth) ---

class UserBase(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class UserRead(UserBase):
    id: int
    is_active: bool
    is_unlocked: bool = False
    plan: Optional[str] = None
    subscription_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class SubscriptionUpdate(BaseModel):
    plan: str
    subscription_id: str
    expires_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    id: Optional[int] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# --- نماذج المهام (Task) ---
class TaskTimerAction(BaseModel):
    """مخطط لتبادل البيانات عند إكمال أو وسم مهمة."""
    progress_details: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "متوسطة"
    due_date: datetime
    category: Optional[str] = "عام"
    estimated_hours: float = Field(default=1.0, gt=0)

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    status: str = "لم تبدأ"
    completed: bool = False
    
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    category: Optional[str] = None
    estimated_hours: Optional[float] = None

class TaskRead(TaskUpdate):
    id: int
    owner_id: int
    created_at: datetime
    is_active: bool
    remaining_time_seconds: int
    time_spent_seconds: int
    start_time: Optional[datetime] = None
    initial_duration_seconds: int
    progress_details: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- نماذج الملاحظات (Note) ---

class NoteBase(BaseModel):
    title: str
    content: str
    category: str = "أفكار"
    is_starred: bool = False

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_starred: Optional[bool] = None

class NoteRead(NoteBase):
    id: int
    owner_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# --- نماذج العادات (Habit) ---

class HabitBase(BaseModel):
    name: str
    category: str = "شخصي"
    days_of_week: str 
    
class HabitCreate(HabitBase):
    pass

class HabitUpdate(HabitBase):
    name: Optional[str] = None
    category: Optional[str] = None
    days_of_week: Optional[str] = None
    current_streak: Optional[int] = None
    best_streak: Optional[int] = None
    last_completed: Optional[datetime] = None
    
class HabitRead(HabitUpdate):
    id: int
    class Config:
        from_attributes = True

# --- نماذج إحصائيات التقارير (Reports) ---

class MonthlyStats(BaseModel):
    completed_tasks: int
    total_tasks: int
    total_hours: float

class CategoryStat(BaseModel):
    name: str
    color: str  # سنضيف لونًا افتراضيًا في الواجهة الخلفية
    completed: int
    total: int
    rate: float

class ReportStats(BaseModel):
    monthly_stats: MonthlyStats
    total_completion_rate: float
    best_habit_streak: int
    category_stats: List[CategoryStat]