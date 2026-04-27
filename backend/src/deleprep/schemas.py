from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    class Config:
        from_attributes = True

class SkillTagSchema(BaseModel):
    id: str
    name: str
    score: float
    category: str
    class Config:
        from_attributes = True

class PromptGenerateRequest(BaseModel):
    taskType: str

class PromptResponse(BaseModel):
    taskType: str
    scenario: str
    bulletPoints: List[str]
    targetSkills: List[str]

class SubmissionRequest(BaseModel):
    submission: str
    prompt: PromptResponse

class InlineCorrection(BaseModel):
    original: str
    correction: str
    explanation: str

class GradingResult(BaseModel):
    score: int
    verdict: str
    corrections: List[InlineCorrection]
    succeededTags: List[str]
    failedTags: List[str]
    overallFeedback: str

class ExamQuestion(BaseModel):
    id: str
    text: str
    options: List[str]
    correct_answer: str
    skill_tag: str
    explanation: str

class ExamGenerateResponse(BaseModel):
    session_id: int
    questions: List[ExamQuestion]

class ExamSubmissionRequest(BaseModel):
    session_id: int
    answers: dict[str, str]  # question_id -> selected_option

class QuestionFeedback(BaseModel):
    question_id: str
    is_correct: bool
    selected_answer: str
    correct_answer: str
    explanation: str
    skill_tag: str
    spaced_repetition_update: str  # e.g., "Review Tomorrow", "Review in 7 days"

class ExamGradingResult(BaseModel):
    score: int
    total_questions: int
    feedback: List[QuestionFeedback]
