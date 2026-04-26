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
