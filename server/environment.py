import random
import uuid
from typing import Any, Dict, Optional

from openenv.core.env_server import Environment

from models import (
    SupportAction,
    SupportObservation,
    SupportState,
)
from tasks import TASKS
from grader import grade_support_action


class SupportTriageEnvironment(Environment):
    """
    Customer support triage environment.

    One episode = one support case.
    The agent gets one case and submits one structured triage action.
    The environment grades it, returns reward, and ends the episode.

    This single-step design is intentionally simple and deterministic for:
    - hackathon speed
    - reproducible grading
    - easy baseline scripting
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        self._state = SupportState()
        self._current_task: Optional[Dict[str, Any]] = None

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        **kwargs: Any,
    ) -> SupportObservation:
        """
        Start a new episode.

        Optional inputs:
        - task_id: choose an exact task
        - difficulty: choose from easy / medium / hard
        - seed: deterministic random selection
        """
        rng = random.Random(seed)

        selected_task = self._select_task(
            rng=rng,
            task_id=task_id,
            difficulty=difficulty,
        )
        self._current_task = selected_task

        obs = selected_task["observation"]

        self._state = SupportState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            case_id=selected_task["task_id"],
            task_id=selected_task["task_id"],
            difficulty=selected_task["difficulty"],
            subject=obs["subject"],
            customer_message=obs["customer_message"],
            customer_tier=obs["customer_tier"],
            order_value=float(obs["order_value"]),
            previous_contact_count=int(obs["previous_contact_count"]),
            has_attachment=bool(obs["has_attachment"]),
            expected_issue_category=selected_task["ground_truth"]["issue_category"],
            expected_priority=selected_task["ground_truth"]["priority"],
            expected_target_team=selected_task["ground_truth"]["target_team"],
            expected_next_action=selected_task["ground_truth"]["next_action"],
            acceptable_issue_categories=selected_task.get(
                "acceptable_alternatives", {}
            ).get("issue_categories", []),
            acceptable_target_teams=selected_task.get(
                "acceptable_alternatives", {}
            ).get("target_teams", []),
            acceptable_next_actions=selected_task.get(
                "acceptable_alternatives", {}
            ).get("next_actions", []),
            final_score=None,
            component_scores={},
            is_terminal=False,
        )

        return self._build_observation(
            message_to_agent=selected_task.get(
                "instructions",
                "Classify the issue, assign priority, route to the correct team, and choose the next action.",
            ),
            reward=0.0,
            done=False,
        )

    def step(
        self,
        action: SupportAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> SupportObservation:
        """
        Submit one triage decision.

        This is a single-step environment:
        - grade once
        - mark episode done
        """
        if self._current_task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        if self._state.is_terminal:
            # Idempotent terminal response: same observation, zero extra reward.
            return self._build_observation(
                message_to_agent="Episode already completed. Call reset() to start a new case.",
                reward=0.0,
                done=True,
            )

        self._state.step_count += 1

        grading_result = grade_support_action(action, self._current_task)

        final_score = float(grading_result["score"])
        self._state.final_score = final_score
        self._state.component_scores = grading_result["component_scores"]
        self._state.is_terminal = True

        feedback_message = self._build_feedback_message(grading_result)

        return self._build_observation(
            message_to_agent=feedback_message,
            reward=final_score,
            done=True,
        )

    @property
    def state(self) -> SupportState:
        return self._state


    def _select_task(
        self,
        rng: random.Random,
        task_id: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> Dict[str, Any]:
        if task_id:
            for task in TASKS:
                if task["task_id"] == task_id:
                    return task
            raise ValueError(f"Unknown task_id: {task_id}")

        filtered = TASKS
        if difficulty:
            difficulty = difficulty.strip().lower()
            filtered = [
                task for task in TASKS
                if task["difficulty"].strip().lower() == difficulty
            ]
            if not filtered:
                raise ValueError(f"No tasks found for difficulty={difficulty}")

        return rng.choice(filtered)

    def _build_observation(
        self,
        message_to_agent: str,
        reward: Optional[float],
        done: bool,
    ) -> SupportObservation:
        return SupportObservation(
            done=done,
            reward=reward,
            case_id=self._state.case_id,
            task_id=self._state.task_id,
            difficulty=self._state.difficulty,  # type: ignore[arg-type]
            subject=self._state.subject,
            customer_message=self._state.customer_message,
            customer_tier=self._state.customer_tier,  # type: ignore[arg-type]
            order_value=self._state.order_value,
            previous_contact_count=self._state.previous_contact_count,
            has_attachment=self._state.has_attachment,
            allowed_issue_categories=[
                "billing",
                "order_status",
                "delivery",
                "returns_refunds",
                "account_security",
                "technical_support",
                "product_issue",
                "other",
            ],
            allowed_priorities=[
                "low",
                "medium",
                "high",
                "critical",
            ],
            allowed_target_teams=[
                "billing_ops",
                "logistics",
                "returns_team",
                "trust_safety",
                "tech_support",
                "general_support",
            ],
            allowed_next_actions=[
                "respond_with_info",
                "request_more_info",
                "escalate",
                "refund_review",
                "replacement_review",
                "security_lock",
                "investigate_account",
                "create_support_ticket",
            ],
            instructions=message_to_agent,
        )

    def _build_feedback_message(self, grading_result: Dict[str, Any]) -> str:
        score = grading_result["score"]
        components = grading_result.get("component_scores", {})
        penalties = grading_result.get("penalties", {})

        parts = [f"Triage completed. Final score: {score:.2f}."]

        if components:
            component_str = ", ".join(
                f"{k}={v:.2f}" for k, v in components.items()
            )
            parts.append(f"Component scores: {component_str}.")

        if penalties:
            penalty_str = ", ".join(
                f"{k}={v:.2f}" for k, v in penalties.items()
            )
            parts.append(f"Penalties applied: {penalty_str}.")
        else:
            parts.append("No penalties applied.")

        return " ".join(parts)