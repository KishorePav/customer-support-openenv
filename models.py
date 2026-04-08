from typing import List, Optional, Literal, Dict, Any
from openenv.core.env_server import Action, Observation, State


IssueCategory = Literal[
    "billing",
    "order_status",
    "delivery",
    "returns_refunds",
    "account_security",
    "technical_support",
    "product_issue",
    "other",
]

PriorityLevel = Literal[
    "low",
    "medium",
    "high",
    "critical",
]

TargetTeam = Literal[
    "billing_ops",
    "logistics",
    "returns_team",
    "trust_safety",
    "tech_support",
    "general_support",
]

NextAction = Literal[
    "respond_with_info",
    "request_more_info",
    "escalate",
    "refund_review",
    "replacement_review",
    "security_lock",
    "investigate_account",
    "create_support_ticket",
]


class SupportAction(Action):
    issue_category: IssueCategory
    priority: PriorityLevel
    target_team: TargetTeam
    next_action: NextAction
    reason: Optional[str] = None


class SupportObservation(Observation):
    case_id: str
    task_id: str
    difficulty: Literal["easy", "medium", "hard"]

    subject: str
    customer_message: str

    customer_tier: Literal["standard", "premium", "vip"]
    order_value: float
    previous_contact_count: int
    has_attachment: bool

    allowed_issue_categories: List[IssueCategory]
    allowed_priorities: List[PriorityLevel]
    allowed_target_teams: List[TargetTeam]
    allowed_next_actions: List[NextAction]

    instructions: str


class SupportState(State):
    case_id: str = ""
    task_id: str = ""
    difficulty: str = ""

    # Internal case data
    subject: str = ""
    customer_message: str = ""
    customer_tier: str = "standard"
    order_value: float = 0.0
    previous_contact_count: int = 0
    has_attachment: bool = False

    # Ground truth for grading
    expected_issue_category: str = ""
    expected_priority: str = ""
    expected_target_team: str = ""
    expected_next_action: str = ""

    # Optional acceptable alternatives
    acceptable_issue_categories: List[str] = []
    acceptable_target_teams: List[str] = []
    acceptable_next_actions: List[str] = []

    # Episode bookkeeping
    final_score: Optional[float] = None
    component_scores: Dict[str, float] = {}
    is_terminal: bool = False