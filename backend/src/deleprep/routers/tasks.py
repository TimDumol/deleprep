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
