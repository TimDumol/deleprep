from pydantic import BaseModel, Field
from typing import Optional

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
    task_type: str = Field(description="The type of writing task to generate, e.g. 'Email' or 'Opinion'.")

class PromptResponse(BaseModel):
    task_type: str = Field(description="The type of writing task generated.")
    scenario: str = Field(description="The specific scenario the student must write about.")
    bullet_points: list[str] = Field(description="A list of bullet points the student must include in their response.")
    target_skills: list[str] = Field(description="The grammar or vocabulary skills this task is designed to practice.")

class SubmissionRequest(BaseModel):
    submission: str = Field(description="The text submitted by the student.")
    prompt: PromptResponse = Field(description="The prompt that the student is responding to.")

class InlineCorrection(BaseModel):
    original: str = Field(description="The original text containing an error.")
    correction: str = Field(description="The corrected version of the text.")
    explanation: str = Field(description="An explanation of why the original text was incorrect.")

class GradingResult(BaseModel):
    score: int = Field(description="The DELE A2 score for the submission, from 0 to 3.")
    verdict: str = Field(description="Pass or Fail.")
    corrections: list[InlineCorrection] = Field(description="A list of specific inline corrections made to the text.")
    succeeded_tags: list[str] = Field(description="The skill tags that the student successfully demonstrated.")
    failed_tags: list[str] = Field(description="The skill tags that the student failed to demonstrate correctly.")
    overall_feedback: str = Field(description="General feedback on the submission.")

class ExamQuestion(BaseModel):
    id: str = Field(description="A unique identifier for the question.")
    text: str = Field(description="The text of the multiple choice question.")
    options: list[str] = Field(description="A list of 4 possible answers.")
    correct_option_index: int = Field(description="The index (0-3) of the correct answer in the options list.")
    skill_tags: list[str] = Field(description="A list of skill tags that this question tests.")
    explanation: str = Field(description="An explanation of why the correct option is correct.")

class ExamGenerateResponse(BaseModel):
    session_id: int = Field(description="The ID of the generated exam session.")
    questions: list[ExamQuestion] = Field(description="The list of questions for the exam.")

class ExamSubmissionRequest(BaseModel):
    session_id: int = Field(description="The ID of the exam session being submitted.")
    answers: dict[str, int] = Field(description="A dictionary mapping question IDs to the selected option index (0-3).")

class QuestionFeedback(BaseModel):
    question_id: str = Field(description="The ID of the question.")
    is_correct: bool = Field(description="Whether the user answered correctly.")
    selected_option_index: int = Field(description="The option index selected by the user.")
    correct_option_index: int = Field(description="The correct option index.")
    explanation: str = Field(description="The explanation for the correct answer.")
    skill_tags: list[str] = Field(description="The skill tags tested by this question.")
    spaced_repetition_update: str = Field(description="Message describing the spaced repetition update, e.g., 'Review Tomorrow'.")

class ExamGradingResult(BaseModel):
    score: int = Field(description="The number of questions answered correctly.")
    total_questions: int = Field(description="The total number of questions in the exam.")
    feedback: list[QuestionFeedback] = Field(description="Detailed feedback for each question.")
