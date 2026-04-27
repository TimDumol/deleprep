from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
from .. import models, schemas, database, ai, auth

router = APIRouter(
    prefix="/api/exams",
    tags=["Exams"]
)

@router.post("/generate", response_model=schemas.ExamGenerateResponse)
async def generate_exam(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = current_user.id

    # Get user's weak skills (e.g. lowest mastery scores, maybe due for review)
    # For now, just pick the 3 lowest mastery score tags to drill down on weak points
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == user_id
    ).order_by(models.UserProgress.mastery_score.asc()).limit(3).all()

    weak_skill_names = []
    for p in progress:
        tag = db.query(models.SkillTag).filter(models.SkillTag.id == p.skill_tag_id).first()
        if tag:
            weak_skill_names.append(tag.name)

    if not weak_skill_names:
        weak_skill_names = ["General A2 Grammar", "General A2 Vocabulary"]

    exam_dict = await ai.generate_exam(weak_skill_names)

    new_session = models.ExamSession(
        user_id=user_id,
        questions=exam_dict["questions"]
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return schemas.ExamGenerateResponse(
        session_id=new_session.id,
        questions=[schemas.ExamQuestion(**q) for q in exam_dict["questions"]]
    )

@router.post("/submit", response_model=schemas.ExamGradingResult)
async def submit_exam(
    request: schemas.ExamSubmissionRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    user_id = current_user.id

    session = db.query(models.ExamSession).filter(
        models.ExamSession.id == request.session_id,
        models.ExamSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    questions = session.questions
    total_questions = len(questions)
    score = 0
    feedback_list = []

    for q in questions:
        q_id = q["id"]
        user_answer = request.answers.get(q_id, "")
        correct_answer = q["correct_answer"]
        is_correct = user_answer == correct_answer

        if is_correct:
            score += 1

        skill_tag_name = q["skill_tag"]
        tag = db.query(models.SkillTag).filter(models.SkillTag.name == skill_tag_name).first()
        spaced_rep_msg = ""

        if tag:
            prog = db.query(models.UserProgress).filter(
                models.UserProgress.user_id == user_id,
                models.UserProgress.skill_tag_id == tag.id
            ).first()

            if prog:
                if is_correct:
                    prog.mastery_score = min(100.0, prog.mastery_score + 2.0)
                    prog.repetition_level += 1
                else:
                    prog.mastery_score = max(0.0, prog.mastery_score - 1.0)
                    prog.repetition_level = max(0, prog.repetition_level - 1)

                # Calculate next review date based on repetition level
                days_to_add = 2 ** prog.repetition_level if prog.repetition_level > 0 else 1
                prog.next_review = datetime.utcnow() + timedelta(days=days_to_add)

                if days_to_add == 1:
                    spaced_rep_msg = "Review Tomorrow"
                else:
                    spaced_rep_msg = f"Review in {days_to_add} days"

        feedback_list.append({
            "question_id": q_id,
            "is_correct": is_correct,
            "selected_answer": user_answer,
            "correct_answer": correct_answer,
            "explanation": q["explanation"],
            "skill_tag": skill_tag_name,
            "spaced_repetition_update": spaced_rep_msg
        })

    # Save submission
    new_submission = models.ExamSubmission(
        exam_session_id=session.id,
        user_id=user_id,
        answers=request.answers,
        score=score,
        total_questions=total_questions,
        feedback=feedback_list
    )
    db.add(new_submission)
    db.commit()

    return schemas.ExamGradingResult(
        score=score,
        total_questions=total_questions,
        feedback=[schemas.QuestionFeedback(**f) for f in feedback_list]
    )
