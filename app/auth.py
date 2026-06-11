from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import database, models

# 🔐 الإعدادات الخاصة بنظام Marco System 2026
SECRET_KEY = "MARCO_SUPER_SECRET_KEY_2026"  # المفتاح السري الموحد للنظام
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# إعداد تشفير كلمة المرور باستخدام معيار bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# دالة التحقق من كلمة المرور (مقارنة النص الصريح بالهاش المخزن)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# دالة تشفير كلمة المرور عند التسجيل لضمان أمان البيانات
def get_password_hash(password):
    return pwd_context.hash(password)

# دالة المصادقة للتحقق من بيانات المستخدم عند تسجيل الدخول
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# دالة إنشاء التوكن (JWT) الذي يستخدمه المتصفح للوصول للمسارات المحمية
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# دالة جلب المستخدم الحالي والتأكد من صلاحية التوكن (Dependency)
def get_current_user(db: Session = Depends(database.get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # فك تشفير التوكن باستخدام المفتاح السري
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # البحث عن المستخدم في قاعدة البيانات بناءً على الاسم الموجود في التوكن
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user