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
