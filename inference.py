import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
from typing import Tuple

import httpx
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:8000").rstrip("/")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

BENCHMARK = os.getenv("BENCHMARK", "customer-support-openenv")
TIMEOUT_S = 60.0
MAX_REASON_CHARS = 300


def require_env(name: str, value: Optional[str]) -> str:
    if not value or not str(value).strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

def build_openai_client() -> OpenAI:
    api_key = require_env("HF_TOKEN", HF_TOKEN)
    require_env("API_BASE_URL", API_BASE_URL)
    require_env("MODEL_NAME", MODEL_NAME)
    return OpenAI(base_url=API_BASE_URL, api_key=api_key)

def get_model_name() -> str:
    return require_env("MODEL_NAME", MODEL_NAME)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Attempts strict JSON parse first.
    Falls back to extracting the outermost JSON object if the model added noise.
    """
    text = text.strip()
    if not text:
        raise ValueError("Empty model response.")

    try:
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("Model response JSON is not an object.")
        return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("Model response is not valid JSON.")


def build_prompt(observation: Dict[str, Any]) -> List[Dict[str, str]]:
    system_prompt = """
You are an expert customer support triage agent.

Your task:
1. Classify the support issue
2. Assign the correct priority
3. Route it to the best target team
4. Select the safest next action

Return ONLY strict JSON in this exact schema:
{
  "issue_category": "...",
  "priority": "...",
  "target_team": "...",
  "next_action": "...",
  "reason": "..."
}

Rules:
- Choose only from the allowed values provided in the observation.
- For security, fraud, or account-takeover style issues, prioritize safety.
- Keep the reason concise and specific.
- Do not include markdown.
- Do not include extra keys.
""".strip()

    user_payload = {
        "case_id": observation.get("case_id"),
        "task_id": observation.get("task_id"),
        "difficulty": observation.get("difficulty"),
        "subject": observation.get("subject"),
        "customer_message": observation.get("customer_message"),
        "customer_tier": observation.get("customer_tier"),
        "order_value": observation.get("order_value"),
        "previous_contact_count": observation.get("previous_contact_count"),
        "has_attachment": observation.get("has_attachment"),
        "allowed_issue_categories": observation.get("allowed_issue_categories", []),
        "allowed_priorities": observation.get("allowed_priorities", []),
        "allowed_target_teams": observation.get("allowed_target_teams", []),
        "allowed_next_actions": observation.get("allowed_next_actions", []),
        "instructions": observation.get("instructions", ""),
    }

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Triage this customer support case and return strict JSON only:\n"
            + json.dumps(user_payload, ensure_ascii=False, indent=2),
        },
    ]


def clamp_action_to_allowed(action: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    allowed_issue_categories = observation.get("allowed_issue_categories", []) or ["other"]
    allowed_priorities = observation.get("allowed_priorities", []) or ["medium"]
    allowed_target_teams = observation.get("allowed_target_teams", []) or ["general_support"]
    allowed_next_actions = observation.get("allowed_next_actions", []) or ["request_more_info"]

    issue_category = str(action.get("issue_category", "")).strip()
    priority = str(action.get("priority", "")).strip()
    target_team = str(action.get("target_team", "")).strip()
    next_action = str(action.get("next_action", "")).strip()
    reason = str(action.get("reason", "")).strip()[:MAX_REASON_CHARS]

    if issue_category not in allowed_issue_categories:
        issue_category = allowed_issue_categories[0]
    if priority not in allowed_priorities:
        priority = allowed_priorities[0]
    if target_team not in allowed_target_teams:
        target_team = allowed_target_teams[0]
    if next_action not in allowed_next_actions:
        next_action = allowed_next_actions[0]
    if not reason:
        reason = "Fallback action due to invalid or incomplete model output."

    return {
        "issue_category": issue_category,
        "priority": priority,
        "target_team": target_team,
        "next_action": next_action,
        "reason": reason,
    }


def default_action(observation: Dict[str, Any], reason: str) -> Dict[str, Any]:
    fallback = clamp_action_to_allowed({}, observation)
    fallback["reason"] = reason[:MAX_REASON_CHARS] or "Fallback action used."
    return fallback


def generate_action(client: OpenAI, observation: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    model_name = get_model_name()
    messages = build_prompt(observation)

    try:
        response = client.chat.completions.create(
            model=model_name,
            temperature=0,
            messages=messages,
        )
        text = response.choices[0].message.content or ""
        parsed = safe_json_loads(text)
        return clamp_action_to_allowed(parsed, observation), None
    except Exception as exc:
        error_msg = str(exc)
        return default_action(
            observation,
            f"Fallback action because model call failed: {error_msg}",
        ), error_msg


def get_tasks(http: httpx.Client) -> List[Dict[str, Any]]:
    response = http.get(f"{ENV_BASE_URL}/tasks")
    response.raise_for_status()

    payload = response.json()
    tasks = payload.get("tasks", [])

    if not isinstance(tasks, list):
        raise RuntimeError("Invalid /tasks response: 'tasks' is not a list.")
    if not tasks:
        raise RuntimeError("No tasks returned from /tasks.")

    return tasks


def reset_task(http: httpx.Client, task_id: str) -> Dict[str, Any]:
    response = http.post(
        f"{ENV_BASE_URL}/reset",
        json={"task_id": task_id},
    )
    response.raise_for_status()

    payload = response.json()

    if isinstance(payload, dict) and "observation" in payload and isinstance(payload["observation"], dict):
        return payload["observation"]

    if isinstance(payload, dict):
        return payload

    raise RuntimeError("Invalid /reset response shape.")


def step_task(http: httpx.Client, action: Dict[str, Any]) -> Dict[str, Any]:
    response = http.post(
        f"{ENV_BASE_URL}/step",
        json={"action": action},
    )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid /step response: expected JSON object.")
    return payload

def action_to_log_string(action: Dict[str, Any]) -> str:
    return json.dumps(action, ensure_ascii=False, separators=(",", ":"))

def run_task(http: httpx.Client, client: OpenAI, task_meta: Dict[str, Any]) -> None:
    task_id = str(task_meta.get("task_id", "")).strip()
    if not task_id:
        raise RuntimeError("Task metadata missing task_id.")

    rewards: List[float] = []
    steps_taken = 0
    success = False
    score = 0.0
    model_name = get_model_name()

    log_start(task=task_id, env=BENCHMARK, model=model_name)

    try:
        observation = reset_task(http, task_id)
        action, model_error  = generate_action(client, observation)
        result = step_task(http, action)

        reward = float(result.get("reward", 0.0))
        done = bool(result.get("done", False))
        error = model_error 

        rewards.append(reward)
        steps_taken = 1

        log_step(
            step=1,
            action=action_to_log_string(action),
            reward=reward,
            done=done,
            error=error,
        )

        score = max(0.0, min(1.0, reward))
        success = done and score > 0.0

    except Exception as exc:
        log_step(
            step=1,
            action="null",
            reward=0.00,
            done=False,
            error=str(exc),
        )
        rewards.append(0.0)
        steps_taken = 1
        score = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

def main() -> int:
    try:
        client = build_openai_client()
        with httpx.Client(timeout=TIMEOUT_S) as http:
            tasks = get_tasks(http)
            for task_meta in tasks:
                run_task(http, client, task_meta)
        return 0
    except Exception as exc:
        print(f"[END] success=false steps=0 score=0.00 rewards= error={exc}", flush=True)
        return 1
    
if __name__ == "__main__":
    sys.exit(main())