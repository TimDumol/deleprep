from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models, schemas, database, auth

router = APIRouter(
    prefix="/api/skills",
    tags=["Skills"]
)

@router.get("/", response_model=list[schemas.SkillTagSchema])
def get_user_skills(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = current_user.id
    progress_records = db.execute(select(models.UserProgress).filter_by(user_id=user_id)).scalars().all()

    result = []
    for p in progress_records:
        tag = db.execute(select(models.SkillTag).filter_by(id=p.skill_tag_id)).scalar_one_or_none()
        if tag:
            result.append(schemas.SkillTagSchema(
                id=tag.id,
                name=tag.name,
                score=p.mastery_score,
                category=tag.category
            ))

    return result
