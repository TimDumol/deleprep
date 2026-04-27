import pytest
from httpx import AsyncClient, ASGITransport
import asyncio
from deleprep.main import app
from deleprep.database import SessionLocal, engine, Base
from deleprep import models, auth
import os

# Ensure clean test DB
Base.metadata.create_all(bind=engine)

def get_test_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dummy auth override
async def override_get_current_user():
    # Return a simple mock object with an id to avoid DetachedInstanceError when the route accesses current_user.id
    class MockUser:
        id = 1

    # Initialize DB state once
    db = SessionLocal()
    try:
        from sqlalchemy import select
        user = db.execute(select(models.User).filter_by(id=1)).scalar_one_or_none()
        if not user:
            user = models.User(id=1, email="test@test.com", hashed_password="pw")
            db.add(user)
            db.commit()

            # Add some tags and progress for testing generate
            tag1 = models.SkillTag(id="test_tag", name="Pretérito Indefinido", category="Grammar")
            tag2 = models.SkillTag(id="test_tag2", name="Pretérito Imperfecto", category="Grammar")
            db.add_all([tag1, tag2])
            db.commit()

            prog1 = models.UserProgress(user_id=1, skill_tag_id="test_tag", mastery_score=10)
            db.add(prog1)
            db.commit()
    finally:
        db.close()

    return MockUser()

app.dependency_overrides[auth.get_current_user] = override_get_current_user

@pytest.mark.asyncio
async def test_generate_and_submit_exam():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Generate Exam
        response = await ac.post("/api/exams/generate")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "questions" in data
        assert len(data["questions"]) == 2

        session_id = data["session_id"]
        q1_id = data["questions"][0]["id"]
        q2_id = data["questions"][1]["id"]

        # Submit Exam
        submit_data = {
            "session_id": session_id,
            "answers": {
                q1_id: 1, # Correct answer for mock LLM
                q2_id: 1  # Incorrect answer for mock LLM
            }
        }

        response = await ac.post("/api/exams/submit", json=submit_data)
        assert response.status_code == 200
        data = response.json()
        assert "score" in data
        assert data["score"] == 1
        assert "total_questions" in data
        assert data["total_questions"] == 2
        assert "feedback" in data
        assert len(data["feedback"]) == 2
