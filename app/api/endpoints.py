from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr
import jwt

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from passlib.context import CryptContext

from app.services.rag_service import stub_rag
from app.services.auth import create_access_token
from app.core.config import settings

router = APIRouter()

# -----------------------------
# Настройка SQLAlchemy для SQLite
# -----------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # БД SQLite в файле test.db
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модель пользователя в базе данных
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

# Создаем таблицы в базе (если их ещё нет)
Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# Хеширование паролей
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------------
# Регистрация пользователя
# -----------------------------
class UserRegister(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    """
    Эндпоинт для регистрации пользователя.
    
    Принимает email и пароль, проверяет наличие email в БД,
    хеширует пароль и сохраняет нового пользователя.
    """
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully."}

# -----------------------------
# Аутентификация и получение токена
# -----------------------------
class TokenLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"

@router.post("/token", response_model=TokenResponse)
def get_token(login_data: TokenLoginRequest, db: Session = Depends(get_db)):
    """
    Эндпоинт для получения JWT токена.
    
    Принимает email и пароль, проверяет наличие пользователя в БД,
    валидирует пароль, а затем возвращает JWT.
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    token = create_access_token(user_identifier=login_data.email)
    return {"access_token": token, "token_type": "Bearer"}

# -----------------------------
# Рабочий функционал RAG-системы
# -----------------------------
class ChatRequest(BaseModel):
    id: str
    question: str
    thread_id: str

class ChatResponse(BaseModel):
    id: str
    answer: str

oauth2_scheme = HTTPBearer()

def verify_token(authorization: dict = Depends(oauth2_scheme)):
    """
    Функция для проверки валидности JWT.
    
    Извлекает payload из токена или выбрасывает исключение, если токен недействительный.
    """
    token: str = authorization.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return payload

@router.post("/chat/send-message", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    token_payload: dict = Depends(verify_token),  # Получаем payload из токена
    db: Session = Depends(get_db)                   # Получаем сессию базы данных
):
    # Предполагается, что в токене хранится email (или другой идентификатор)
    user_email = token_payload.get("user_identifier")
    if not user_email:
        raise HTTPException(status_code=400, detail="Invalid token payload")
    
    # Ищем пользователя по email
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Получаем ответ от RAG-системы (stub_rag)
    # Здесь stub_rag принимает данные запроса и возвращает словарь, в котором ожидается ключ "answer"
    rag_response = stub_rag(request_data=request.dict())
    
    # Формируем ответ, где id пользователя берётся из БД, а ответ из системы RAG.
    return ChatResponse(
        id=rag_response.get('id'),              # Используем идентификатор пользователя из базы данных
        answer=rag_response.get("answer", "No answer provided")  # Используем ключ "answer" из ответа RAG
    )