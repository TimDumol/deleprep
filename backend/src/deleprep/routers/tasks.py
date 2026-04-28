from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from .. import models, schemas, database, ai, auth

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"]
)

@router.post("/generate", response_model=schemas.PromptResponse)
async def generate_task_prompt(
    request: schemas.PromptGenerateRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = current_user.id
    stmt = select(models.UserProgress).filter_by(user_id=user_id).order_by(models.UserProgress.mastery_score.asc()).limit(3)
    progress = db.execute(stmt).scalars().all()

    weak_skill_names = []
    for p in progress:
        tag = db.execute(select(models.SkillTag).filter_by(id=p.skill_tag_id)).scalar_one_or_none()
        if tag:
            weak_skill_names.append(tag.name)

    prompt_dict = await ai.generate_prompt(request.task_type, weak_skill_names)

    new_submission = models.TaskSubmission(
        user_id=user_id,
        task_type=prompt_dict["task_type"],
        scenario=prompt_dict["scenario"],
        bullet_points=prompt_dict["bullet_points"],
        target_skills=prompt_dict["target_skills"]
    )
    db.add(new_submission)
    db.commit()

    return schemas.PromptResponse(**prompt_dict)

@router.post("/submit", response_model=schemas.GradingResult)
async def submit_task(
    request: schemas.SubmissionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = current_user.id
    grading_dict = await ai.grade_submission(request.submission, request.prompt.target_skills)

    stmt = select(models.TaskSubmission).filter_by(
        user_id=user_id,
        task_type=request.prompt.task_type,
        submission_text=None
    ).order_by(models.TaskSubmission.id.desc())
    submission = db.execute(stmt).scalars().first()

    if submission:
        submission.submission_text = request.submission
        submission.score = grading_dict["score"]
        submission.verdict = grading_dict["verdict"]
        submission.succeeded_tags = grading_dict["succeeded_tags"]
        submission.failed_tags = grading_dict["failed_tags"]
        submission.overall_feedback = grading_dict["overall_feedback"]

        for corr in grading_dict["corrections"]:
            db_corr = models.Correction(
                submission_id=submission.id,
                original=corr["original"],
                correction=corr["correction"],
                explanation=corr["explanation"]
            )
            db.add(db_corr)

        for success_tag_name in grading_dict["succeeded_tags"]:
            tag = db.execute(select(models.SkillTag).filter_by(name=success_tag_name)).scalar_one_or_none()
            if tag:
                prog = db.execute(select(models.UserProgress).filter_by(
                    user_id=user_id, skill_tag_id=tag.id
                )).scalar_one_or_none()
                if prog:
                    prog.mastery_score = min(100.0, prog.mastery_score + 5.0)

        for failed_tag_name in grading_dict["failed_tags"]:
            tag = db.execute(select(models.SkillTag).filter_by(name=failed_tag_name)).scalar_one_or_none()
            if tag:
                prog = db.execute(select(models.UserProgress).filter_by(
                    user_id=user_id, skill_tag_id=tag.id
                )).scalar_one_or_none()
                if prog:
                    prog.mastery_score = max(0.0, prog.mastery_score - 2.0)

        db.commit()

    return schemas.GradingResult(**grading_dict)
