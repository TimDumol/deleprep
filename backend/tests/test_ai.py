import pytest
from deleprep.ai import generate_prompt, grade_submission
import os
os.environ["OPENAI_BASE_URL"] = "http://localhost:8080/v1"
os.environ["OPENAI_API_KEY"] = "mock"

@pytest.mark.asyncio
async def test_generate_prompt():
    res = await generate_prompt("Email", ["Pretérito Indefinido"])
    assert "task_type" in res
    assert res["task_type"] == "Task 1: Email"
    assert "bullet_points" in res
    assert len(res["bullet_points"]) == 4

@pytest.mark.asyncio
async def test_grade_submission():
    res = await grade_submission("El hotel tuvo una piscina", ["Pretérito Imperfecto"])
    assert "score" in res
    assert res["score"] == 2
    assert "corrections" in res
    assert len(res["corrections"]) == 1
    assert "overall_feedback" in res
