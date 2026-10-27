
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4

from agent import evaluate_mission
from assessment_agent import (
    AssessmentRequest,
    generate_assessment,
    evaluate_assessment_answers,
)

app = FastAPI(title="AI Quest Evaluation Agent")

# Temporary server-side storage.
# Data resets whenever the server restarts.
assessment_store = {}


class EvaluationRequest(BaseModel):
    mission: str
    prompt_used: str
    ai_output: str
    time_before: int = Field(ge=0)
    time_after: int = Field(ge=0)
    fact_checking: str
    creative_approach: str


class AssessmentSubmission(BaseModel):
    assessment_id: str
    answers: dict[str, str]


@app.get("/")
def home():
    return {"message": "AI Quest Evaluation Agent is running"}


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
    try:
        return evaluate_mission(request.mission, submission)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(error)}"
        )


@app.post("/assessment/generate")
def create_assessment(request: AssessmentRequest):
    try:
        questions = generate_assessment(request)
        assessment_id = str(uuid4())

        # Keep the complete answer key on the server.
        assessment_store[assessment_id] = {
            "course_name": request.course_name,
            "department": request.department,
            "job_role": request.job_role,
            "questions": [
                question.model_dump()
                for question in questions
            ]
        }

        # Send only employee-facing question fields.
        safe_questions = []
        for question in questions:
            safe_questions.append({
                "question_id": question.question_id,
                "question": question.question,
                "question_type": question.question_type,
                "options": question.options,
                "marks": question.marks,
                "topic": question.topic
            })

        return {
            "assessment_id": assessment_id,
            "course_name": request.course_name,
            "department": request.department,
            "job_role": request.job_role,
            "questions": safe_questions
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment generation failed: {str(error)}"
        )


@app.post("/assessment/submit")
def submit_assessment(request: AssessmentSubmission):
    assessment = assessment_store.get(request.assessment_id)

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment not found. Generate a new assessment first."
        )

    try:
        result = evaluate_assessment_answers(
            assessment["questions"],
            request.answers
        )
        return {
            "assessment_id": request.assessment_id,
            "course_name": assessment["course_name"],
            **result
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Assessment submission failed: {str(error)}"
        )
