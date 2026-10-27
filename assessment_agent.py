
import os
import re
import json
from typing import List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field


# -------------------------------
# 1. Assessment data models
# -------------------------------

class AssessmentQuestion(BaseModel):
    question_id: str
    question: str
    question_type: str
    options: List[str] = Field(default_factory=list)
    marks: int = 2
    correct_answer: Optional[str] = None
    rubric: Optional[str] = None
    topic: str = "General"


class AssessmentRequest(BaseModel):
    department: str
    job_role: str
    course_name: str
    learning_objectives: List[str]
    number_of_questions: int = Field(default=5, ge=1, le=20)


# -------------------------------
# 2. Validate assessment request
# -------------------------------

def validate_assessment_request(request):
    if not request.department.strip():
        raise ValueError("Department is required.")

    if not request.job_role.strip():
        raise ValueError("Job role is required.")

    if not request.course_name.strip():
        raise ValueError("Course name is required.")

    if not request.learning_objectives:
        raise ValueError("At least one learning objective is required.")

    if any(not item.strip() for item in request.learning_objectives):
        raise ValueError("Learning objectives cannot be empty.")

    return True


# -------------------------------
# 3. Generate local practice questions
# -------------------------------

def generate_local_assessment(request):
    """Generate practice questions without requiring API credits."""

    questions = []

    for i in range(request.number_of_questions):
        objective = request.learning_objectives[
            i % len(request.learning_objectives)
        ].strip()

        topic = objective

        for prefix in (
            "understand ",
            "learn ",
            "explain ",
            "describe ",
            "know "
        ):
            if topic.lower().startswith(prefix):
                topic = topic[len(prefix):].strip()
                break

        topic_lower = topic.lower()

        if "variable" in topic_lower:
            question_text = (
                f"What are {topic}? Explain their use in "
                f"{request.course_name} with an example."
            )

        elif "loop" in topic_lower and "condition" in topic_lower:
            question_text = (
                f"How do {topic} work in {request.course_name}? "
                "Explain with a simple example."
            )

        elif "loop" in topic_lower:
            question_text = (
                f"What is {topic}? Explain how it works "
                "with a practical example."
            )

        else:
            question_text = (
                f"Explain {topic} in {request.course_name} "
                "and give one practical example."
            )

        questions.append(
            AssessmentQuestion(
                question_id=f"Q{i + 1}",
                question=question_text,
                question_type="short_answer",
                options=[],
                marks=2,
                correct_answer=None,
                rubric=(
                    f"The answer should accurately explain {topic} "
                    "and provide a relevant example."
                ),
                topic=topic
            )
        )

    return questions


# -------------------------------
# 4. Generate assessment
# -------------------------------

def generate_assessment(request):
    validate_assessment_request(request)

    test_mode = os.getenv(
        "ASSESSMENT_TEST_MODE", "true"
    ).lower() == "true"

    # Local mode works without API credits.
    if test_mode:
        return generate_local_assessment(request)

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is missing. Configure an API key "
            "or enable ASSESSMENT_TEST_MODE=true."
        )

    client = OpenAI(api_key=api_key)

    prompt = f"""
Create exactly {request.number_of_questions} assessment questions.

Department: {request.department}
Job role: {request.job_role}
Course: {request.course_name}
Learning objectives: {request.learning_objectives}

Return valid JSON only in this format:
{{
  "questions": [
    {{
      "question_id": "Q1",
      "question": "Question text",
      "question_type": "short_answer",
      "options": [],
      "marks": 2,
      "correct_answer": null,
      "rubric": "Expected answer criteria",
      "topic": "Topic"
    }}
  ]
}}

Allowed types: mcq, true_false, short_answer, scenario.
Match questions to the course, role and learning objectives.
For MCQs and true/false questions, provide the correct answer.
For descriptive questions, provide a grading rubric.
Do not invent facts or claim external verification.
"""

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=prompt
    )

    try:
        data = json.loads(response.output_text)
        raw_questions = data.get("questions", [])

        if len(raw_questions) != request.number_of_questions:
            raise ValueError(
                "The AI returned an incorrect number of questions."
            )

        return [
            AssessmentQuestion(**question)
            for question in raw_questions
        ]

    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError(
            "The AI response was not valid assessment JSON."
        ) from error


# -------------------------------
# 5. Evaluate submitted answers
# -------------------------------

def evaluate_assessment_answers(questions, answers):
    """
    Local keyword-based test evaluator.
    This is not a real AI correctness evaluator.
    """

    stop_words = {
        "understand", "explain", "describe", "learn", "know",
        "the", "a", "an", "of", "and", "or", "to", "for",
        "whether", "correctly", "check", "this", "that",
        "objective", "objectives", "course", "with", "from",
        "what", "how", "their", "they", "are", "is", "in",
        "one", "give", "example", "practical", "relevant",
        "accurately", "should", "answer", "provide", "works"
    }

    def keywords(text):
        words = re.findall(r"[a-zA-Z]+", text.lower())
        result = set()

        for word in words:
            if word in stop_words:
                continue

            if word.endswith("ies") and len(word) > 4:
                word = word[:-3] + "y"
            elif (
                word.endswith("s")
                and not word.endswith("ss")
                and len(word) > 3
            ):
                word = word[:-1]

            result.add(word)

        return result

    results = []
    total_marks = 0
    marks_obtained = 0

    for question in questions:
        question_id = question["question_id"]
        answer = answers.get(question_id, "").strip()
        max_marks = int(question.get("marks", 1))

        total_marks += max_marks

        if not answer:
            score = 0
            feedback = "Answer not provided."

        else:
            topic_words = keywords(question.get("topic", ""))

            if not topic_words:
                score = 0
                feedback = "No topic keywords available for checking."

            else:
                answer_words = keywords(answer)
                matched = topic_words.intersection(answer_words)

                score = round(
                    max_marks * len(matched) / len(topic_words)
                )
                score = max(0, min(max_marks, score))

                if score == max_marks:
                    feedback = (
                        "Topic keywords matched. This is a local "
                        "test score, not an AI-verified correctness score."
                    )
                elif score > 0:
                    feedback = (
                        "Some topic keywords matched. "
                        "Manual review recommended."
                    )
                else:
                    feedback = (
                        "No topic keywords matched. "
                        "Manual review recommended."
                    )

        marks_obtained += score

        results.append({
            "question_id": question_id,
            "marks_obtained": score,
            "maximum_marks": max_marks,
            "feedback": feedback
        })

    percentage = (
        round((marks_obtained / total_marks) * 100, 2)
        if total_marks > 0 else 0
    )

    return {
        "marks_obtained": marks_obtained,
        "total_marks": total_marks,
        "percentage": percentage,
        "evaluation_mode": "local_keyword_test",
        "results": results
    }
