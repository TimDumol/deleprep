from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .routers import auth, skills, tasks
from .database import engine, Base, SessionLocal
from . import models, auth as auth_utils
from .config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DELE A2 Prep API")

@app.on_event("startup")
def create_dummy_user():
    db = SessionLocal()
    try:
        # Check by email first, then by ID to allow email updates or ID mismatch
        user = db.query(models.User).filter(models.User.email == settings.test_user_email).first()
        if not user:
            user = db.query(models.User).filter(models.User.id == 1).first()

        hashed_pw = auth_utils.get_password_hash(settings.test_user_password)

        if not user:
            # Auto-create user with email and hashed password if missing
            dummy_user = models.User(id=1, email=settings.test_user_email, hashed_password=hashed_pw)
            db.add(dummy_user)
            db.commit()

            # Optionally populate some tags to avoid foreign key errors on progress
            tags = db.query(models.SkillTag).all()
            if not tags:
                new_tags = [
                    models.SkillTag(id="1", name="Pretérito Indefinido", category="Grammar"),
                    models.SkillTag(id="2", name="Pretérito Imperfecto", category="Grammar"),
                    models.SkillTag(id="3", name="Vocabulary: Work/Study", category="Vocabulary"),
                    models.SkillTag(id="4", name="Connectors", category="Cohesion")
                ]
                db.add_all(new_tags)
                db.commit()
                tags = new_tags

            # Populate initial progress for the dummy user
            progress = [
                models.UserProgress(user_id=1, skill_tag_id="1", mastery_score=45),
                models.UserProgress(user_id=1, skill_tag_id="2", mastery_score=50),
                models.UserProgress(user_id=1, skill_tag_id="3", mastery_score=65),
                models.UserProgress(user_id=1, skill_tag_id="4", mastery_score=80)
            ]
            db.add_all(progress)
            db.commit()
    finally:
        db.close()

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
