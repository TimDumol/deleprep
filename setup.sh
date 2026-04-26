#!/bin/bash
set -e

# 1. Docker compose setup
cat << 'DOCKER' > docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: deleprep_user
      POSTGRES_PASSWORD: deleprep_password
      POSTGRES_DB: deleprep_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
DOCKER
sudo su -c "echo '{ \"storage-driver\": \"vfs\" }' > /etc/docker/daemon.json" && sudo systemctl restart docker
docker compose up -d

# 2. Python env and dependencies
cd backend
cat << 'PYPROJ' > pyproject.toml
[project]
name = "deleprep"
version = "0.1.0"
description = "DELE A2 Prep Backend"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110.0",
    "sqlalchemy>=2.0.29",
    "alembic>=1.13.1",
    "psycopg2-binary>=2.9.9",
    "pydantic>=2.6.4",
    "pydantic-settings>=2.2.1",
    "uvicorn>=0.29.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt==4.0.1",
    "python-jose[cryptography]>=3.3.0",
    "python-multipart>=0.0.9"
]

[project.scripts]
deleprep = "deleprep:main"

[build-system]
requires = ["uv_build>=0.11.7,<0.12.0"]
build-backend = "uv_build"
PYPROJ

uv sync

# 3. Backend files
mkdir -p src/deleprep/routers
cat << 'ENVFILE' > .env
SECRET_KEY=my_super_secret_key_development
DATABASE_URL=postgresql://deleprep_user:deleprep_password@localhost/deleprep_db
ENVFILE

cat << 'CONF' > src/deleprep/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "my_super_secret_key_development"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "postgresql://deleprep_user:deleprep_password@localhost/deleprep_db"

    class Config:
        env_file = ".env"

settings = Settings()
CONF

cat << 'DB' > src/deleprep/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
DB

cat << 'MODELS' > src/deleprep/models.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, JSON
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    progress = relationship("UserProgress", back_populates="user")
    submissions = relationship("TaskSubmission", back_populates="user")

class SkillTag(Base):
    __tablename__ = "skill_tags"
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    category = Column(String)
    parent_id = Column(String, ForeignKey("skill_tags.id"), nullable=True)
    children = relationship("SkillTag", back_populates="parent")
    parent = relationship("SkillTag", back_populates="children", remote_side=[id])

class UserProgress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    skill_tag_id = Column(String, ForeignKey("skill_tags.id"))
    mastery_score = Column(Float, default=0.0)
    user = relationship("User", back_populates="progress")
    skill_tag = relationship("SkillTag")

class TaskSubmission(Base):
    __tablename__ = "task_submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_type = Column(String)
    scenario = Column(String)
    bullet_points = Column(JSON)
    target_skills = Column(JSON)
    submission_text = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    verdict = Column(String, nullable=True)
    succeeded_tags = Column(JSON, nullable=True)
    failed_tags = Column(JSON, nullable=True)
    overall_feedback = Column(String, nullable=True)
    user = relationship("User", back_populates="submissions")
    corrections = relationship("Correction", back_populates="submission")

class Correction(Base):
    __tablename__ = "corrections"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("task_submissions.id"))
    original = Column(String)
    correction = Column(String)
    explanation = Column(String)
    submission = relationship("TaskSubmission", back_populates="corrections")
MODELS

cat << 'SCHEMAS' > src/deleprep/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class SkillTagSchema(BaseModel):
    id: str
    name: str
    score: float
    category: str
    class Config:
        from_attributes = True

class PromptGenerateRequest(BaseModel):
    taskType: str

class PromptResponse(BaseModel):
    taskType: str
    scenario: str
    bulletPoints: List[str]
    targetSkills: List[str]

class SubmissionRequest(BaseModel):
    submission: str
    prompt: PromptResponse

class InlineCorrection(BaseModel):
    original: str
    correction: str
    explanation: str

class GradingResult(BaseModel):
    score: int
    verdict: str
    corrections: List[InlineCorrection]
    succeededTags: List[str]
    failedTags: List[str]
    overallFeedback: str
SCHEMAS

cat << 'AUTH' > src/deleprep/auth.py
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, database
from .config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
AUTH

cat << 'AI' > src/deleprep/ai.py
import asyncio
from typing import List, Dict

async def generate_prompt(task_type: str, weak_skills: List[str]) -> Dict:
    await asyncio.sleep(0.5)
    if "Email" in task_type:
        return {
            "taskType": "Task 1: Email",
            "scenario": "Write an email to a friend telling them about a recent trip you took.",
            "bulletPoints": [
                "Where did you go and when?",
                "What did you do there? (Use Pretérito Indefinido)",
                "What was the place like? (Use Pretérito Imperfecto)",
                "Suggest a plan to meet and show them photos."
            ],
            "targetSkills": weak_skills if weak_skills else ["Pretérito Indefinido", "Pretérito Imperfecto"]
        }
    else:
        return {
            "taskType": "Task 2: Narrative",
            "scenario": "Write a short story about your first day at a new job or school.",
            "bulletPoints": [
                "Describe the setting and how you felt. (Use Pretérito Imperfecto)",
                "Explain what happened during the day. (Use Pretérito Indefinido)",
                "Mention who you met and what they were like.",
                "Say how the day ended."
            ],
            "targetSkills": weak_skills if weak_skills else ["Pretérito Indefinido", "Pretérito Imperfecto", "Vocabulary: Work/Study"]
        }

async def grade_submission(submission_text: str, target_skills: List[str]) -> Dict:
    await asyncio.sleep(0.5)
    return {
        "score": 2,
        "verdict": "Pass",
        "corrections": [
            {
                "original": "El hotel era muy bonito y tuvo una piscina.",
                "correction": "El hotel era muy bonito y tenía una piscina.",
                "explanation": "Use Pretérito Imperfecto (\"tenía\") for descriptions in the past, not Indefinido (\"tuvo\")."
            },
            {
                "original": "Yo fui al playa todos los días.",
                "correction": "Yo fui a la playa todos los días.",
                "explanation": "\"Playa\" is feminine, so use \"a la\" instead of \"al\" (a + el)."
            }
        ],
        "succeededTags": [target_skills[0]] if target_skills else ["Pretérito Indefinido"],
        "failedTags": [target_skills[1]] if len(target_skills) > 1 else ["Pretérito Imperfecto"],
        "overallFeedback": "Good effort! You successfully used the Pretérito Indefinido to narrate events, but remember to use the Pretérito Imperfecto for descriptions in the past."
    }
AI

touch src/deleprep/routers/__init__.py
cat << 'ROUTERA' > src/deleprep/routers/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, auth, database

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    tags = db.query(models.SkillTag).all()
    for tag in tags:
        progress = models.UserProgress(user_id=new_user.id, skill_tag_id=tag.id, mastery_score=50.0)
        db.add(progress)
    db.commit()
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
ROUTERA

cat << 'ROUTERS' > src/deleprep/routers/skills.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth

router = APIRouter(
    prefix="/api/skills",
    tags=["Skills"]
)

@router.get("/", response_model=List[schemas.SkillTagSchema])
def get_user_skills(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    progress_records = db.query(models.UserProgress).filter(models.UserProgress.user_id == current_user.id).all()

    result = []
    for p in progress_records:
        tag = db.query(models.SkillTag).filter(models.SkillTag.id == p.skill_tag_id).first()
        if tag:
            result.append(schemas.SkillTagSchema(
                id=tag.id,
                name=tag.name,
                score=p.mastery_score,
                category=tag.category
            ))

    return result
ROUTERS

cat << 'ROUTERT' > src/deleprep/routers/tasks.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas, database, auth, ai

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"]
)

@router.post("/generate", response_model=schemas.PromptResponse)
async def generate_task_prompt(
    request: schemas.PromptGenerateRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id
    ).order_by(models.UserProgress.mastery_score.asc()).limit(3).all()

    weak_skill_names = []
    for p in progress:
        tag = db.query(models.SkillTag).filter(models.SkillTag.id == p.skill_tag_id).first()
        if tag:
            weak_skill_names.append(tag.name)

    prompt_dict = await ai.generate_prompt(request.taskType, weak_skill_names)

    new_submission = models.TaskSubmission(
        user_id=current_user.id,
        task_type=prompt_dict["taskType"],
        scenario=prompt_dict["scenario"],
        bullet_points=prompt_dict["bulletPoints"],
        target_skills=prompt_dict["targetSkills"]
    )
    db.add(new_submission)
    db.commit()

    return schemas.PromptResponse(**prompt_dict)

@router.post("/submit", response_model=schemas.GradingResult)
async def submit_task(
    request: schemas.SubmissionRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    grading_dict = await ai.grade_submission(request.submission, request.prompt.targetSkills)

    submission = db.query(models.TaskSubmission).filter(
        models.TaskSubmission.user_id == current_user.id,
        models.TaskSubmission.task_type == request.prompt.taskType,
        models.TaskSubmission.submission_text.is_(None)
    ).order_by(models.TaskSubmission.id.desc()).first()

    if submission:
        submission.submission_text = request.submission
        submission.score = grading_dict["score"]
        submission.verdict = grading_dict["verdict"]
        submission.succeeded_tags = grading_dict["succeededTags"]
        submission.failed_tags = grading_dict["failedTags"]
        submission.overall_feedback = grading_dict["overallFeedback"]

        for corr in grading_dict["corrections"]:
            db_corr = models.Correction(
                submission_id=submission.id,
                original=corr["original"],
                correction=corr["correction"],
                explanation=corr["explanation"]
            )
            db.add(db_corr)

        for success_tag_name in grading_dict["succeededTags"]:
            tag = db.query(models.SkillTag).filter(models.SkillTag.name == success_tag_name).first()
            if tag:
                prog = db.query(models.UserProgress).filter(
                    models.UserProgress.user_id == current_user.id,
                    models.UserProgress.skill_tag_id == tag.id
                ).first()
                if prog:
                    prog.mastery_score = min(100.0, prog.mastery_score + 5.0)

        for failed_tag_name in grading_dict["failedTags"]:
            tag = db.query(models.SkillTag).filter(models.SkillTag.name == failed_tag_name).first()
            if tag:
                prog = db.query(models.UserProgress).filter(
                    models.UserProgress.user_id == current_user.id,
                    models.UserProgress.skill_tag_id == tag.id
                ).first()
                if prog:
                    prog.mastery_score = max(0.0, prog.mastery_score - 2.0)

        db.commit()

    return schemas.GradingResult(**grading_dict)
ROUTERT

cat << 'MAIN' > src/deleprep/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, skills, tasks
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DELE A2 Prep API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(skills.router)
app.include_router(tasks.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
MAIN

cat << 'RUN' > run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("deleprep.main:app", host="0.0.0.0", port=8000, reload=True)
RUN

uv run alembic init alembic
cat << 'ALEMBICENV' > alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

import os
import sys
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../src')))
from deleprep.models import Base
from deleprep.config import settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
ALEMBICENV

uv run alembic revision --autogenerate -m "Init"
uv run alembic upgrade head

cat << 'SEED' > src/deleprep/seed.py
from sqlalchemy.orm import Session
from .database import engine, SessionLocal
from . import models, auth

def seed_db():
    db = SessionLocal()

    if db.query(models.SkillTag).first():
        print("Database already seeded")
        db.close()
        return

    tags = [
        models.SkillTag(id="1", name="Pretérito Indefinido", category="Grammar"),
        models.SkillTag(id="2", name="Pretérito Imperfecto", category="Grammar"),
        models.SkillTag(id="3", name="Vocabulary: Work/Study", category="Vocabulary"),
        models.SkillTag(id="4", name="Connectors", category="Cohesion")
    ]
    db.add_all(tags)
    db.commit()

    hashed_password = auth.get_password_hash("password123")
    user = models.User(email="test@example.com", hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    progress = [
        models.UserProgress(user_id=user.id, skill_tag_id="1", mastery_score=45),
        models.UserProgress(user_id=user.id, skill_tag_id="2", mastery_score=50),
        models.UserProgress(user_id=user.id, skill_tag_id="3", mastery_score=65),
        models.UserProgress(user_id=user.id, skill_tag_id="4", mastery_score=80)
    ]
    db.add_all(progress)
    db.commit()

    print("Database seeded successfully")
    db.close()

if __name__ == "__main__":
    seed_db()
SEED

uv run python -m deleprep.seed

uv run python run.py > uvicorn.log 2>&1 &
cd ..

# 4. Frontend updates
cd frontend
cat << 'VCONFIG' > vite.config.ts
import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'
import { tanstackStart } from '@tanstack/react-start/plugin/vite'
import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const config = defineConfig({
  resolve: { tsconfigPaths: true },
  plugins: [devtools(), tailwindcss(), tanstackStart(), viteReact()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
export default config
VCONFIG

sed -i "s/import { useState } from 'react'/import { useState, useEffect } from 'react'/" src/routes/index.tsx
sed -i "s/{mockSkills/{skills/g" src/routes/index.tsx

cat << 'EOF' > patch_app.py
import re

with open('src/routes/index.tsx', 'r') as f:
    content = f.read()

replacement = """
  const [token, setToken] = useState<string | null>(null)
  const [skills, setSkills] = useState<SkillTag[]>([])

  const fetchSkills = async (currentToken: string) => {
    try {
      const skillsRes = await fetch('/api/skills/', {
        headers: { Authorization: `Bearer ${currentToken}` },
      })
      const skillsData = await skillsRes.json()
      setSkills(skillsData)
    } catch (err) {
      console.error('Failed to fetch skills', err)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        const formData = new URLSearchParams()
        formData.append('username', 'test@example.com')
        formData.append('password', 'password123')

        const loginRes = await fetch('/api/auth/login', {
          method: 'POST',
          body: formData,
        })
        const loginData = await loginRes.json()
        const accessToken = loginData.access_token
        setToken(accessToken)

        await fetchSkills(accessToken)
      } catch (err) {
        console.error('Failed to initialize login', err)
      }
    }
    init()
  }, [])

  const handleTaskSelect = async (task: string) => {
    setSelectedTask(task)
    setAppState('generating')

    try {
      const res = await fetch('/api/tasks/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ taskType: task }),
      })
      const data = await res.json()
      setPrompt(data)
      setAppState('writing')
    } catch (err) {
      console.error(err)
      setAppState('select-task')
    }
  }

  const handleSubmit = async () => {
    setAppState('grading')

    try {
      const res = await fetch('/api/tasks/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ submission, prompt }),
      })
      const data = await res.json()
      setGrading(data)
      setAppState('feedback')
    } catch (err) {
      console.error(err)
      setAppState('writing')
    }
  }

  const handleReset = () => {
    setAppState('select-task')
    setSelectedTask(null)
    setPrompt(null)
    setSubmission('')
    setGrading(null)

    if (token) {
      fetchSkills(token)
    }
  }
"""

pattern = re.compile(r'  // Simulation handlers\n  const handleTaskSelect.*?setGrading\(null\)\n  }', re.DOTALL)
new_content = pattern.sub(replacement.strip(), content)

with open('src/routes/index.tsx', 'w') as f:
    f.write(new_content)
