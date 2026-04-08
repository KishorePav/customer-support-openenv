from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from server.environment import SupportTriageEnvironment
from tasks import TASKS
from models import SupportAction
from grader import grade_support_action

app = FastAPI(title="Customer Support Triage OpenEnv")

env = SupportTriageEnvironment()


class ResetRequest(BaseModel):
    task_id: Optional[str] = None
    difficulty: Optional[str] = None
    seed: Optional[int] = None
    episode_id: Optional[str] = None


class StepRequest(BaseModel):
    action: SupportAction


class GraderRequest(BaseModel):
    task_id: str
    action: SupportAction


class BaselineResponse(BaseModel):
    status: str
    message: str
    tasks_evaluated: int


def _get_task_by_id(task_id: str) -> Dict[str, Any]:
    for task in TASKS:
        if task["task_id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")


@app.get("/")
def root() -> Dict[str, str]:
    return {
        "name": "Customer Support Triage OpenEnv",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks() -> Dict[str, Any]:
    return {
        "count": len(TASKS),
        "action_schema": {
            "issue_category": [
                "billing",
                "order_status",
                "delivery",
                "returns_refunds",
                "account_security",
                "technical_support",
                "product_issue",
                "other",
            ],
            "priority": ["low", "medium", "high", "critical"],
            "target_team": [
                "billing_ops",
                "logistics",
                "returns_team",
                "trust_safety",
                "tech_support",
                "general_support",
            ],
            "next_action": [
                "respond_with_info",
                "request_more_info",
                "escalate",
                "refund_review",
                "replacement_review",
                "security_lock",
                "investigate_account",
                "create_support_ticket",
            ],
            "reason": "optional string",
        },
        "tasks": [
            {
                "task_id": task["task_id"],
                "difficulty": task["difficulty"],
                "title": task["title"],
                "instructions": task.get("instructions", ""),
            }
            for task in TASKS
        ],
    }


@app.post("/reset")
def reset_endpoint(payload: ResetRequest) -> Dict[str, Any]:
    try:
        obs = env.reset(
            task_id=payload.task_id,
            difficulty=payload.difficulty,
            seed=payload.seed,
            episode_id=payload.episode_id,
        )
        return {"observation": obs.model_dump()}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/step")
def step_endpoint(payload: StepRequest) -> Dict[str, Any]:
    try:
        obs = env.step(payload.action)
        return {
            "observation": obs.model_dump(),
            "reward": obs.reward,
            "done": obs.done,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/state")
def state_endpoint() -> Dict[str, Any]:
    return env.state.model_dump()


@app.post("/grader")
def grader_endpoint(payload: GraderRequest) -> Dict[str, Any]:
    task = _get_task_by_id(payload.task_id)
    result = grade_support_action(payload.action, task)
    return {
        "task_id": payload.task_id,
        "difficulty": task["difficulty"],
        "title": task["title"],
        "grading_result": result,
    }


@app.post("/baseline", response_model=BaselineResponse)
def baseline_endpoint() -> BaselineResponse:
    return BaselineResponse(
        status="not_implemented",
        message="Baseline runner not wired yet. Use inference.py directly for now.",
        tasks_evaluated=len(TASKS),
    )

def main() -> None:
    uvicorn.run("server.app:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()