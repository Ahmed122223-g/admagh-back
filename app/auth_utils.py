# app/auth_utils.py - الكود النهائي باستخدام PBKDF2-SHA256

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

load_dotenv()

# --- إعدادات JWT (بدون تغيير) ---
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- إعداد تجزئة كلمة المرور ---
# تغيير Scheme إلى pbkdf2_sha256
# هذه الخوارزمية لا تفرض قيود 72 بايت وأكثر استقرارًا على Windows/Linux.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# --- دوال المصادقة المصححة ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من كلمة المرور العادية مقابل المجزأة"""
    try:
        # لا نحتاج لتقييد الطول هنا
        return pwd_context.verify(plain_password, hashed_password)
    except:
        return False

def get_password_hash(password: str) -> str:
    """تجزئة كلمة المرور"""
    # لا نحتاج لتقييد الطول هنا
    return pwd_context.hash(password)

# --- وظائف JWT (بدون تغيير) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode.update({"exp": expire, "sub": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None