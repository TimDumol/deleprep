from fastapi import FastAPI, Request
from pydantic import BaseModel
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ChatCompletionRequest(BaseModel):
    model: str
    messages: list
    response_format: dict | None = None

@app.post("/v1/chat/completions")
async def create_chat_completion(request: Request):
    body = await request.json()
    logger.info(f"Received request: {json.dumps(body)}")

    # Very simple mock based on system prompt or messages content
    messages = body.get("messages", [])
    system_prompt = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")

    if "Generate a writing task" in system_prompt:
        # Prompt generation mock response
        mock_response = {
            "taskType": "Task 1: Email",
            "scenario": "Write an email to a friend telling them about a recent trip you took.",
            "bulletPoints": [
                "Where did you go and when?",
                "What did you do there? (Use Pretérito Indefinido)",
                "What was the place like? (Use Pretérito Imperfecto)",
                "Suggest a plan to meet and show them photos."
            ],
            "targetSkills": ["Pretérito Indefinido", "Pretérito Imperfecto"]
        }
    else:
        # Grading mock response
        mock_response = {
            "score": 2,
            "verdict": "Pass",
            "corrections": [
                {
                    "original": "El hotel era muy bonito y tuvo una piscina.",
                    "correction": "El hotel era muy bonito y tenía una piscina.",
                    "explanation": "Use Pretérito Imperfecto (\"tenía\") for descriptions in the past, not Indefinido (\"tuvo\")."
                }
            ],
            "succeededTags": ["Pretérito Indefinido"],
            "failedTags": ["Pretérito Imperfecto"],
            "overallFeedback": "Good effort!"
        }

    return {
        "id": "chatcmpl-mock",
        "object": "chat.completion",
        "created": 1700000000,
        "model": body.get("model", "gpt-4o-mini"),
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps(mock_response),
                    "function_call": None,
                    "tool_calls": None
                },
                "logprobs": None,
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        },
        "system_fingerprint": None
    }
