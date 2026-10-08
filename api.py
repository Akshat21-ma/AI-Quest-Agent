from fastapi import FastAPI
from pydantic import BaseModel
from agent import evaluate_mission

app = FastAPI(title="AI Quest Evaluation Agent")


class EvaluationRequest(BaseModel):
    mission: str
    prompt_used: str
    ai_output: str
    time_before: int
    time_after: int
    fact_checking: str
    creative_approach: str


@app.get("/")
def home():
    return {
        "message": "AI Quest Evaluation Agent is running"
    }


@app.post("/evaluate")
def evaluate(request: EvaluationRequest):

    submission = f"""
PROMPT USED:
{request.prompt_used}

AI OUTPUT:
{request.ai_output}

TIME BEFORE AI:
{request.time_before} minutes

TIME AFTER AI:
{request.time_after} minutes

FACT CHECKING:
{request.fact_checking}

CREATIVE APPROACH:
{request.creative_approach}
"""

    result = evaluate_mission(
        request.mission,
        submission
    )

    return result