from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def evaluate_mission(mission, submission):

    evaluation_prompt = f"""
You are an AI Quest mission evaluation agent.

Evaluate the employee's AI mission submission based ONLY on the evidence provided.

MISSION:
{mission}

EMPLOYEE SUBMISSION:
{submission}


Evaluate these 5 criteria from 0 to 10:

1. Prompt Quality
2. Output Quality
3. Time Saved
4. Fact Checking
5. Creativity


SCORING RULES:

PROMPT QUALITY:
Check whether the employee provides a clear, specific and useful AI prompt.

OUTPUT QUALITY:
Check whether the actual AI-generated output is provided and whether it is useful,
relevant and appropriate for the mission.

TIME SAVED:
Use TIME BEFORE AI and TIME AFTER AI.
Consider how much time was saved and the percentage improvement.

FACT CHECKING:
Check whether the employee explains how AI-generated information was verified
against the original or reliable source.

CREATIVITY:
Check whether the employee used a creative, innovative or better-than-standard
approach.

IMPORTANT RULES:
- Score ONLY using evidence in the submission.
- Do NOT invent missing information.
- Missing evidence should receive a low score.
- Scores must be between 0 and 10.
- Give a short reason for every score.
- Do NOT calculate total_xp yourself.
- Give practical suggestions for improving weak areas.
- Return valid JSON only.


Return exactly this structure:

{{
  "prompt_quality": {{
    "score": 0,
    "reason": ""
  }},
  "output_quality": {{
    "score": 0,
    "reason": ""
  }},
  "time_saved": {{
    "score": 0,
    "reason": ""
  }},
  "fact_checking": {{
    "score": 0,
    "reason": ""
  }},
  "creativity": {{
    "score": 0,
    "reason": ""
  }},
  "overall_feedback": "",
  "improvement_suggestions": [
    "",
    "",
    ""
  ]
}}
"""

    response = client.responses.create(
        model="gpt-6-luna",
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

        score = result[criterion]["score"]

        score = max(0, min(10, int(score)))

        result[criterion]["score"] = score

        total_xp += score

    result["total_xp"] = total_xp

    return result


if __name__ == "__main__":

    print("AI Quest Evaluation Agent")

    mission = input("\nEnter Mission: ")

    prompt_used = input("\nEnter Prompt Used: ")

    ai_output = input("\nEnter AI Output: ")

    time_before = input("\nTime Before AI (minutes): ")

    time_after = input("\nTime After AI (minutes): ")

    fact_checking = input("\nFact Checking: ")

    creative_approach = input("\nCreative Approach: ")

    submission = f"""
PROMPT USED:
{prompt_used}

AI OUTPUT:
{ai_output}

TIME BEFORE AI:
{time_before} minutes

TIME AFTER AI:
{time_after} minutes

FACT CHECKING:
{fact_checking}

CREATIVE APPROACH:
{creative_approach}
"""

    print("\nEvaluating submission...")

    result = evaluate_mission(mission, submission)

    print("\n========================================")

    for criterion in [
        "prompt_quality",
        "output_quality",
        "time_saved",
        "fact_checking",
        "creativity"
    ]:

        print(
            f"{criterion.replace('_', ' ').title()}: "
            f"{result[criterion]['score']} /10"
        )

        print(
            f"Reason: {result[criterion]['reason']}"
        )

        print()

    print("----------------------------------------")

    print(f"TOTAL XP: {result['total_xp']} /50")

    print("\nOVERALL FEEDBACK:")
    print(result["overall_feedback"])

    print("\nIMPROVEMENT SUGGESTIONS:")

    for suggestion in result["improvement_suggestions"]:
        print(f"- {suggestion}")

    print("========================================")