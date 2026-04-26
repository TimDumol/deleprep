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
