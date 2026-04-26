import asyncio
from typing import List, Dict

async def generate_prompt(task_type: str, weak_skills: List[str]) -> Dict:
    await asyncio.sleep(0.5)
    if "Email" in task_type:
        return {
            "taskType": "Task 1: Email",
            "scenario": "Write an email to a friend telling them about a recent trip you took.",
            "bulletPoints": [
                "Where did you go and when?",
                "What did you do there? (Use Pretérito Indefinido)",
                "What was the place like? (Use Pretérito Imperfecto)",
                "Suggest a plan to meet and show them photos."
            ],
            "targetSkills": weak_skills if weak_skills else ["Pretérito Indefinido", "Pretérito Imperfecto"]
        }
    else:
        return {
            "taskType": "Task 2: Narrative",
            "scenario": "Write a short story about your first day at a new job or school.",
            "bulletPoints": [
                "Describe the setting and how you felt. (Use Pretérito Imperfecto)",
                "Explain what happened during the day. (Use Pretérito Indefinido)",
                "Mention who you met and what they were like.",
                "Say how the day ended."
            ],
            "targetSkills": weak_skills if weak_skills else ["Pretérito Indefinido", "Pretérito Imperfecto", "Vocabulary: Work/Study"]
        }

async def grade_submission(submission_text: str, target_skills: List[str]) -> Dict:
    await asyncio.sleep(0.5)
    return {
        "score": 2,
        "verdict": "Pass",
        "corrections": [
            {
                "original": "El hotel era muy bonito y tuvo una piscina.",
                "correction": "El hotel era muy bonito y tenía una piscina.",
                "explanation": "Use Pretérito Imperfecto (\"tenía\") for descriptions in the past, not Indefinido (\"tuvo\")."
            },
            {
                "original": "Yo fui al playa todos los días.",
                "correction": "Yo fui a la playa todos los días.",
                "explanation": "\"Playa\" is feminine, so use \"a la\" instead of \"al\" (a + el)."
            }
        ],
        "succeededTags": [target_skills[0]] if target_skills else ["Pretérito Indefinido"],
        "failedTags": [target_skills[1]] if len(target_skills) > 1 else ["Pretérito Imperfecto"],
        "overallFeedback": "Good effort! You successfully used the Pretérito Indefinido to narrate events, but remember to use the Pretérito Imperfecto for descriptions in the past."
    }
