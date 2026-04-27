from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta
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

    # Get all valid skills for the LLM
    all_tags = db.execute(select(models.SkillTag)).scalars().all()
    valid_skill_names = [t.name for t in all_tags]

    # Get user's weak skills (e.g. lowest mastery scores, maybe due for review)
    # For now, just pick the 3 lowest mastery score tags to drill down on weak points
    stmt = select(models.UserProgress).filter_by(user_id=user_id).order_by(models.UserProgress.mastery_score.asc()).limit(3)
    progress = db.execute(stmt).scalars().all()

    weak_skill_names = []
    for p in progress:
        tag = db.execute(select(models.SkillTag).filter_by(id=p.skill_tag_id)).scalar_one_or_none()
        if tag:
            weak_skill_names.append(tag.name)

    if not weak_skill_names:
        weak_skill_names = ["General A2 Grammar", "General A2 Vocabulary"]
        valid_skill_names.extend(weak_skill_names) # In case they aren't seeded

    exam_dict = await ai.generate_exam(weak_skill_names, valid_skill_names)

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

    session = db.execute(
        select(models.ExamSession).filter_by(id=request.session_id, user_id=user_id)
    ).scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Exam session not found")

    questions = session.questions
    total_questions = len(questions)
    score = 0
    feedback_list = []

    # Track performance per tag across the entire exam to do bulk updates
    # so multiple questions on the same skill don't push repetition out wildly
    tag_performance = {} # tag_name -> {'correct': int, 'incorrect': int}

    for q in questions:
        q_id = q["id"]
        user_answer_idx = request.answers.get(q_id, -1)
        correct_idx = q["correct_option_index"]
        is_correct = user_answer_idx == correct_idx

        if is_correct:
            score += 1

        skill_tags = q.get("skill_tags", [])
        for t in skill_tags:
            if t not in tag_performance:
                tag_performance[t] = {'correct': 0, 'incorrect': 0}
            if is_correct:
                tag_performance[t]['correct'] += 1
            else:
                tag_performance[t]['incorrect'] += 1

        feedback_list.append({
            "question_id": q_id,
            "is_correct": is_correct,
            "selected_option_index": user_answer_idx,
            "correct_option_index": correct_idx,
            "explanation": q.get("explanation", ""),
            "skill_tags": skill_tags,
            "spaced_repetition_update": "Pending..." # Overwritten shortly
        })

    # Bulk update skill tags progress
    tag_messages = {}
    for tag_name, perfs in tag_performance.items():
        tag = db.execute(select(models.SkillTag).filter_by(name=tag_name)).scalar_one_or_none()
        if tag:
            prog = db.execute(select(models.UserProgress).filter_by(user_id=user_id, skill_tag_id=tag.id)).scalar_one_or_none()
            if prog:
                # Net impact on repetition
                net_correct = perfs['correct'] - perfs['incorrect']
                if net_correct > 0:
                    prog.mastery_score = min(100.0, prog.mastery_score + 2.0)
                    prog.repetition_level += 1
                elif net_correct < 0:
                    prog.mastery_score = max(0.0, prog.mastery_score - 1.0)
                    prog.repetition_level = max(0, prog.repetition_level - 1)
                # If net 0, leave repetition alone but maybe adjust score slightly? Let's leave both alone.

                days_to_add = 2 ** prog.repetition_level if prog.repetition_level > 0 else 1
                prog.next_review = datetime.utcnow() + timedelta(days=days_to_add)

                if days_to_add == 1:
                    tag_messages[tag_name] = "Review Tomorrow"
                else:
                    tag_messages[tag_name] = f"Review in {days_to_add} days"

    # Populate final spaced repetition strings
    for f in feedback_list:
        msgs = []
        for t in f["skill_tags"]:
            if t in tag_messages:
                msgs.append(f"{t}: {tag_messages[t]}")
        if msgs:
            f["spaced_repetition_update"] = " | ".join(msgs)
        else:
            f["spaced_repetition_update"] = "No update"

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
