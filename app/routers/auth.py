# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from ..database import get_db
from ..auth_utils import create_access_token, verify_password, get_password_hash
from .. import crud, schemas
from ..dependencies import ActiveUser
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["المصادقة (Auth)"],
)

@router.post("/signup", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def signup(
    user: schemas.UserCreate, 
    db: Session = Depends(get_db)
):
    """إنشاء حساب مستخدم جديد"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مستخدم بالفعل",
        )
    return crud.create_user(db=db, user=user)

@router.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Session = Depends(get_db) 
):
    """تسجيل دخول المستخدم وإصدار رمز JWT"""
    
    # form_data هو الوسيط الأول لأنه لا يحمل قيمة افتراضية مباشرة
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="بيانات الاعتماد غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"email": user.email, "user_id": user.id}
    )
    
    return schemas.Token(access_token=access_token, token_type="bearer")



@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user: schemas.UserRead = Depends(ActiveUser)):
    """Return current authenticated user's profile"""
    return current_user

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    passwords: schemas.PasswordChange,
    db: Session = Depends(get_db),
    current_user: schemas.UserRead = Depends(ActiveUser)
):
    """تغيير كلمة مرور المستخدم الحالي"""
    user = crud.get_user_by_email(db, email=current_user.email)
    if not user or not verify_password(passwords.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="كلمة المرور القديمة غير صحيحة",
        )
    
    hashed_password = get_password_hash(passwords.new_password)
    user.hashed_password = hashed_password
    db.commit()
    
    return {"message": "تم تغيير كلمة المرور بنجاح"}