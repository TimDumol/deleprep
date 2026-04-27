from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from .config import settings
import json

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

class PromptResponse(BaseModel):
    task_type: str = Field(description="The type of writing task generated.")
    scenario: str = Field(description="The specific scenario the student must write about.")
    bullet_points: list[str] = Field(description="A list of bullet points the student must include in their response.")
    target_skills: list[str] = Field(description="The grammar or vocabulary skills this task is designed to practice.")

class Correction(BaseModel):
    original: str = Field(description="The original text containing an error.")
    correction: str = Field(description="The corrected version of the text.")
    explanation: str = Field(description="An explanation of why the original text was incorrect.")

class GradeResponse(BaseModel):
    score: int = Field(description="The DELE A2 score for the submission, from 0 to 3.")
    verdict: str = Field(description="Pass or Fail.")
    corrections: list[Correction] = Field(description="A list of specific inline corrections made to the text.")
    succeeded_tags: list[str] = Field(description="The skill tags that the student successfully demonstrated.")
    failed_tags: list[str] = Field(description="The skill tags that the student failed to demonstrate correctly.")
    overall_feedback: str = Field(description="General feedback on the submission.")

class ExamQuestionParsed(BaseModel):
    id: str = Field(description="A unique identifier for the question.")
    text: str = Field(description="The text of the multiple choice question.")
    options: list[str] = Field(description="A list of 4 possible answers.")
    correct_option_index: int = Field(description="The index (0-3) of the correct answer in the options list.")
    skill_tags: list[str] = Field(description="A list of skill tags that this question tests. MUST ONLY use tags from the provided list.")
    explanation: str = Field(description="An explanation of why the correct option is correct.")

class ExamGenerateParsed(BaseModel):
    questions: list[ExamQuestionParsed] = Field(description="The list of questions for the exam.")

async def generate_prompt(task_type: str, weak_skills: list[str]) -> dict:
    system_prompt = (
        "You are a helpful assistant for DELE A2 writing preparation. "
        "Generate a writing task for a student based on their requested task type and their weak skills. "
        "The response MUST be a JSON object with 'task_type', 'scenario', 'bullet_points', and 'target_skills'."
    )
    user_prompt = f"Task type: {task_type}. Weak skills: {weak_skills}"

    completion = await client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=PromptResponse,
    )

    return json.loads(completion.choices[0].message.content)

async def generate_exam(weak_skills: list[str], valid_skills: list[str]) -> dict:
    system_prompt = (
        "You are an expert DELE A2 examiner. "
        "Generate a targeted multiple-choice exam focusing on the student's weak skills. "
        "The response MUST be a JSON object with 'questions', which is a list of objects containing "
        "'id' (string), 'text' (the question), 'options' (list of 4 string options), "
        "'correct_option_index' (integer 0-3), 'skill_tags' (list of strings matching the target skills), "
        "and 'explanation' (string explaining why the answer is correct). "
        f"You MUST ONLY use skill tags from this valid list: {valid_skills}"
    )
    user_prompt = f"Weak skills: {weak_skills}"

    completion = await client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=ExamGenerateParsed,
    )

    return json.loads(completion.choices[0].message.content)

async def grade_submission(submission_text: str, target_skills: list[str]) -> dict:
    system_prompt = (
        "You are an expert DELE A2 examiner. "
        "Evaluate the student's submission text based on DELE A2 rubrics (Coherence, Fluency, Correctness, Scope). "
        "The response MUST be a JSON object with 'score' (0-3), 'verdict' (Pass/Fail), "
        "'corrections' (list of {original, correction, explanation}), 'succeeded_tags', "
        "'failed_tags', and 'overall_feedback'."
    )
    user_prompt = f"Target skills: {target_skills}\n\nSubmission: {submission_text}"

    completion = await client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=GradeResponse,
    )

    return json.loads(completion.choices[0].message.content)
