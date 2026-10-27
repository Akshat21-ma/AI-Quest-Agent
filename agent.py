
from openai import OpenAI
import os
import json


def evaluate_mission(mission, submission):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY missing hai. Environment variable configure karo."
        )

    client = OpenAI(api_key=api_key)

    evaluation_prompt = f"""
You are an AI Quest mission evaluation agent.

Evaluate the employee submission using ONLY the evidence provided.

MISSION:
{mission}

EMPLOYEE SUBMISSION:
{submission}

Score these five criteria from 0 to 10:
1. Prompt Quality
2. Output Quality
3. Time Saved
4. Fact Checking
5. Creativity

Rules:
- Use only evidence in the submission.
- Do not invent missing information.
- Give low scores when evidence is missing.
- Give a short reason for each score.
- Time Saved must use TIME BEFORE AI and TIME AFTER AI.
- Do not calculate total_xp.
- Give practical improvement suggestions.
- Return valid JSON only.

Return exactly this structure:
{{
  "prompt_quality": {{"score": 0, "reason": ""}},
  "output_quality": {{"score": 0, "reason": ""}},
  "time_saved": {{"score": 0, "reason": ""}},
  "fact_checking": {{"score": 0, "reason": ""}},
  "creativity": {{"score": 0, "reason": ""}},
  "overall_feedback": "",
  "improvement_suggestions": ["", "", ""]
}}
"""

    try:
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
            input=evaluation_prompt
        )

        result = json.loads(response.output_text)

        criteria = [
            "prompt_quality",
            "output_quality",
            "time_saved",
            "fact_checking",
            "creativity"
        ]

        total_xp = 0

        for criterion in criteria:
            if criterion not in result:
                raise ValueError(
                    f"AI response mein {criterion} missing hai."
                )

            item = result[criterion]

            if not isinstance(item, dict) or "score" not in item:
                raise ValueError(
                    f"{criterion} ka score invalid hai."
                )

            score = int(item["score"])
            score = max(0, min(10, score))

            item["score"] = score
            item.setdefault("reason", "")
            total_xp += score

        result.setdefault("overall_feedback", "")
        result.setdefault("improvement_suggestions", [])
        result["total_xp"] = total_xp

        return result

    except json.JSONDecodeError as error:
        raise ValueError(
            "AI ne valid JSON response nahi diya."
        ) from error

    except Exception as error:
        raise RuntimeError(
            f"Mission evaluation failed: {error}"
        ) from error


if __name__ == "__main__":
    print("AI Quest Evaluation Agent")
    print("Is file ko direct run karne ke liye API key zaroori hai.")
