from passlib.context import CryptContext
from datetime import datetime,timedelta
from typing import Optional
from jose import jwt, JWTError

# Password hashing setup
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

#JWT Configurations
SECRET_kEY = 'your_secret_key_here'
ALGORITHM = 'HS256'
# ACCESS_TOKEN_EXPIRY_TIME = 30
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_password(plain_pwd:str,hased_pwd:str) -> bool:
    return pwd_context.verify(plain_pwd,hased_pwd)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict,expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT access token.
    'data' should contain the user's identity (e.g., username or user_id).
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})

    encode_jwt = jwt.encode(to_encode,SECRET_kEY,algorithm=ALGORITHM)
    return encode_jwt

def decode_access_token(token:str):
    try:
        payload = jwt.decode(token,SECRET_kEY,algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None