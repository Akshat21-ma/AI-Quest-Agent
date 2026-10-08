# AI Quest Evaluation Agent

## Overview

The AI Quest Evaluation Agent evaluates employee submissions for AI-based missions.

It evaluates the submission using five criteria:

1. Prompt Quality
2. Output Quality
3. Time Saved
4. Fact Checking
5. Creativity

Each criterion is scored from 0 to 10.

Maximum Score: 50 XP

## Evaluation Flow

Mission
    ↓
Employee Submission
    ↓
AI Evaluation Agent
    ↓
5 Criteria Evaluation
    ↓
Total XP
    ↓
Feedback
    ↓
Improvement Suggestions

## API

The agent provides a FastAPI endpoint:

POST /evaluate

## Request Fields

The API accepts:

- mission
- prompt_used
- ai_output
- time_before
- time_after
- fact_checking
- creative_approach

## Response

The agent returns:

- Prompt Quality score
- Output Quality score
- Time Saved score
- Fact Checking score
- Creativity score
- Total XP out of 50
- Overall Feedback
- Improvement Suggestions

## How to Run

Activate the virtual environment:

```powershell
venv\Scripts\activate