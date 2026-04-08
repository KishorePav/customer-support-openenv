from typing import Any, Dict

from models import SupportAction


DEFAULT_WEIGHTS = {
    "issue_category": 0.3,
    "priority": 0.2,
    "target_team": 0.2,
    "next_action": 0.3,
}


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _score_exact_or_alternative(
    predicted: str,
    expected: str,
    alternatives: list[str] | None,
    exact_score: float = 1.0,
    alternative_score: float = 0.5,
) -> float:
    predicted_n = _normalize(predicted)
    expected_n = _normalize(expected)
    alternatives_n = {_normalize(v) for v in (alternatives or [])}

    if predicted_n == expected_n:
        return exact_score

    if predicted_n in alternatives_n:
        return alternative_score

    return 0.0


def _priority_score(predicted: str, expected: str) -> float:
    """
    Priority is graded a bit smarter than exact match.

    Exact match -> 1.0
    One level away -> 0.5
    More than one level away -> 0.0
    """
    levels = ["low", "medium", "high", "critical"]
    predicted_n = _normalize(predicted)
    expected_n = _normalize(expected)

    if predicted_n not in levels or expected_n not in levels:
        return 0.0

    if predicted_n == expected_n:
        return 1.0

    distance = abs(levels.index(predicted_n) - levels.index(expected_n))
    if distance == 1:
        return 0.5

    return 0.0


def _compute_penalties(
    action: SupportAction,
    task: Dict[str, Any],
) -> Dict[str, float]:
    """
    Returns named penalties. Values are additive negatives later.
    """
    penalties: Dict[str, float] = {}

    risk_flags = task.get("risk_flags", {})
    ground_truth = task.get("ground_truth", {})

    predicted_priority = _normalize(action.priority)
    predicted_team = _normalize(action.target_team)
    predicted_next_action = _normalize(action.next_action)

    expected_priority = _normalize(ground_truth.get("priority"))
    expected_team = _normalize(ground_truth.get("target_team"))
    expected_next_action = _normalize(ground_truth.get("next_action"))

    is_security_sensitive = bool(risk_flags.get("is_security_sensitive", False))
    is_financial_sensitive = bool(risk_flags.get("is_financial_sensitive", False))
    requires_escalation = bool(risk_flags.get("requires_escalation", False))

    # Penalty 1: under-prioritizing security-sensitive issues
    if is_security_sensitive and predicted_priority in {"low", "medium"}:
        penalties["underprioritized_security_case"] = -0.30

    # Penalty 2: under-prioritizing urgent financial issues
    if is_financial_sensitive and expected_priority in {"high", "critical"}:
        if predicted_priority in {"low", "medium"}:
            penalties["underprioritized_financial_case"] = -0.20

    # Penalty 3: routing security cases away from trust/safety
    if is_security_sensitive and predicted_team != "trust_safety":
        penalties["unsafe_team_routing"] = -0.25

    # Penalty 4: cases requiring escalation but agent chooses a passive action
    if requires_escalation and predicted_next_action in {
        "respond_with_info",
        "request_more_info",
    }:
        penalties["failed_to_escalate"] = -0.20

    # Penalty 5: if the action is especially unsafe for a critical case
    if expected_priority == "critical" and predicted_priority == "low":
        penalties["severely_underprioritized_critical_case"] = -0.30

    # Penalty 6: mild penalty for completely wrong next action in high-risk cases
    if requires_escalation and predicted_next_action not in {
        expected_next_action,
        "escalate",
        "security_lock",
        "investigate_account",
    }:
        penalties["unsafe_next_action"] = -0.15

    return penalties


def grade_support_action(
    action: SupportAction,
    task: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Grades a SupportAction against one task definition.

    Returns:
    {
        "score": float,                  # final clipped 0.0..1.0
        "raw_score": float,              # before clipping
        "component_scores": {...},       # weighted component contributions
        "component_details": {...},      # unweighted match scores
        "penalties": {...},              # named penalties
        "ground_truth": {...},           # expected answers
    }
    """
    ground_truth = task["ground_truth"]
    alternatives = task.get("acceptable_alternatives", {})
    weights = task.get("grading_weights", DEFAULT_WEIGHTS)

    # Unweighted match scores in 0.0..1.0
    issue_category_match = _score_exact_or_alternative(
        predicted=action.issue_category,
        expected=ground_truth["issue_category"],
        alternatives=alternatives.get("issue_categories", []),
        exact_score=1.0,
        alternative_score=0.5,
    )

    priority_match = _priority_score(
        predicted=action.priority,
        expected=ground_truth["priority"],
    )

    target_team_match = _score_exact_or_alternative(
        predicted=action.target_team,
        expected=ground_truth["target_team"],
        alternatives=alternatives.get("target_teams", []),
        exact_score=1.0,
        alternative_score=0.5,
    )

    next_action_match = _score_exact_or_alternative(
        predicted=action.next_action,
        expected=ground_truth["next_action"],
        alternatives=alternatives.get("next_actions", []),
        exact_score=1.0,
        alternative_score=0.5,
    )

    component_details = {
        "issue_category_match": issue_category_match,
        "priority_match": priority_match,
        "target_team_match": target_team_match,
        "next_action_match": next_action_match,
    }

    # Weighted contributions
    component_scores = {
        "issue_category": issue_category_match * weights["issue_category"],
        "priority": priority_match * weights["priority"],
        "target_team": target_team_match * weights["target_team"],
        "next_action": next_action_match * weights["next_action"],
    }

    positive_score = sum(component_scores.values())

    penalties = _compute_penalties(action=action, task=task)
    penalty_total = sum(penalties.values())

    raw_score = positive_score + penalty_total
    final_score = max(0.0, min(1.0, raw_score))

    return {
        "score": round(final_score, 4),
        "raw_score": round(raw_score, 4),
        "component_scores": {k: round(v, 4) for k, v in component_scores.items()},
        "component_details": {k: round(v, 4) for k, v in component_details.items()},
        "penalties": {k: round(v, 4) for k, v in penalties.items()},
        "ground_truth": ground_truth,
    }