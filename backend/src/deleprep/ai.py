from typing import List, Dict
from pydantic import BaseModel
from openai import AsyncOpenAI
from .config import settings
import json

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

class PromptResponse(BaseModel):
    taskType: str
    scenario: str
    bulletPoints: List[str]
    targetSkills: List[str]

class Correction(BaseModel):
    original: str
    correction: str
    explanation: str

class GradeResponse(BaseModel):
    score: int
    verdict: str
    corrections: List[Correction]
    succeededTags: List[str]
    failedTags: List[str]
    overallFeedback: str

class ExamQuestionParsed(BaseModel):
    id: str
    text: str
    options: List[str]
    correct_answer: str
    skill_tag: str
    explanation: str

class ExamGenerateParsed(BaseModel):
    questions: List[ExamQuestionParsed]

async def generate_prompt(task_type: str, weak_skills: List[str]) -> Dict:
    system_prompt = (
        "You are a helpful assistant for DELE A2 writing preparation. "
        "Generate a writing task for a student based on their requested task type and their weak skills. "
        "The response MUST be a JSON object with 'taskType', 'scenario', 'bulletPoints', and 'targetSkills'."
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

async def generate_exam(weak_skills: List[str]) -> Dict:
    system_prompt = (
        "You are an expert DELE A2 examiner. "
        "Generate a targeted multiple-choice exam focusing on the student's weak skills. "
        "The response MUST be a JSON object with 'questions', which is a list of objects containing "
        "'id' (string), 'text' (the question), 'options' (list of 4 string options), "
        "'correct_answer' (string matching one option), 'skill_tag' (string matching the target skill), "
        "and 'explanation' (string explaining why the answer is correct)."
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

async def grade_submission(submission_text: str, target_skills: List[str]) -> Dict:
    system_prompt = (
        "You are an expert DELE A2 examiner. "
        "Evaluate the student's submission text based on DELE A2 rubrics (Coherence, Fluency, Correctness, Scope). "
        "The response MUST be a JSON object with 'score' (0-3), 'verdict' (Pass/Fail), "
        "'corrections' (list of {original, correction, explanation}), 'succeededTags', "
        "'failedTags', and 'overallFeedback'."
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
