from typing import List, Dict, Any

TASKS: List[Dict[str, Any]] = [

    # -------------------------
    # EASY TASKS
    # -------------------------

    {
        "task_id": "easy_001",
        "difficulty": "easy",
        "title": "Double charge on one order",

        "observation": {
            "subject": "Charged twice for one order",
            "customer_message": "I placed one order but my card was charged twice. Please fix this.",
            "customer_tier": "standard",
            "order_value": 2499.0,
            "previous_contact_count": 0,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "billing",
            "priority": "high",
            "target_team": "billing_ops",
            "next_action": "refund_review"
        },

        "acceptable_alternatives": {
            "issue_categories": [],
            "target_teams": ["general_support"],
            "next_actions": ["create_support_ticket"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": True,
            "is_multi_intent": False,
            "requires_escalation": False
        },

        "instructions": "Classify the issue, assign priority, select target team, and choose next action."
    },

    {
        "task_id": "easy_002",
        "difficulty": "easy",
        "title": "Package marked delivered but not received",

        "observation": {
            "subject": "Order marked delivered but not received",
            "customer_message": "The app says my order was delivered but I haven't received anything.",
            "customer_tier": "standard",
            "order_value": 899.0,
            "previous_contact_count": 0,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "delivery",
            "priority": "medium",
            "target_team": "logistics",
            "next_action": "investigate_account"
        },

        "acceptable_alternatives": {
            "issue_categories": ["order_status"],
            "target_teams": ["general_support"],
            "next_actions": ["create_support_ticket"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": False,
            "is_multi_intent": False,
            "requires_escalation": False
        },

        "instructions": "Determine delivery issue and route correctly."
    },

    {
        "task_id": "easy_003",
        "difficulty": "easy",
        "title": "Damaged product return",

        "observation": {
            "subject": "Received damaged product",
            "customer_message": "The product I received is broken and unusable. I want a replacement.",
            "customer_tier": "premium",
            "order_value": 1599.0,
            "previous_contact_count": 0,
            "has_attachment": True
        },

        "ground_truth": {
            "issue_category": "product_issue",
            "priority": "medium",
            "target_team": "returns_team",
            "next_action": "replacement_review"
        },

        "acceptable_alternatives": {
            "issue_categories": ["returns_refunds"],
            "target_teams": ["general_support"],
            "next_actions": ["create_support_ticket"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": False,
            "is_multi_intent": False,
            "requires_escalation": False
        },

        "instructions": "Handle product issue and suggest replacement."
    },

    # -------------------------
    # MEDIUM TASKS
    # -------------------------

    {
        "task_id": "medium_001",
        "difficulty": "medium",
        "title": "Charged but order not visible",

        "observation": {
            "subject": "Payment done but no order",
            "customer_message": "I was charged but I cannot see my order in the app.",
            "customer_tier": "standard",
            "order_value": 1999.0,
            "previous_contact_count": 1,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "billing",
            "priority": "high",
            "target_team": "billing_ops",
            "next_action": "investigate_account"
        },

        "acceptable_alternatives": {
            "issue_categories": ["order_status"],
            "target_teams": ["general_support"],
            "next_actions": ["create_support_ticket"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": True,
            "is_multi_intent": True,
            "requires_escalation": False
        },

        "instructions": "Resolve mismatch between payment and order visibility."
    },

    {
        "task_id": "medium_002",
        "difficulty": "medium",
        "title": "Refund denied for defective product",

        "observation": {
            "subject": "Refund rejected",
            "customer_message": "My refund request was rejected even though the product was defective.",
            "customer_tier": "premium",
            "order_value": 1299.0,
            "previous_contact_count": 2,
            "has_attachment": True
        },

        "ground_truth": {
            "issue_category": "returns_refunds",
            "priority": "medium",
            "target_team": "returns_team",
            "next_action": "refund_review"
        },

        "acceptable_alternatives": {
            "issue_categories": ["product_issue"],
            "target_teams": ["general_support"],
            "next_actions": ["create_support_ticket"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": True,
            "is_multi_intent": True,
            "requires_escalation": False
        },

        "instructions": "Handle refund dispute appropriately."
    },

    {
        "task_id": "medium_003",
        "difficulty": "medium",
        "title": "Delayed order with no response",

        "observation": {
            "subject": "Order delayed",
            "customer_message": "My order is delayed and I haven't received any updates.",
            "customer_tier": "standard",
            "order_value": 799.0,
            "previous_contact_count": 2,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "delivery",
            "priority": "medium",
            "target_team": "logistics",
            "next_action": "investigate_account"
        },

        "acceptable_alternatives": {
            "issue_categories": ["order_status"],
            "target_teams": ["general_support"],
            "next_actions": ["request_more_info"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": False,
            "is_multi_intent": False,
            "requires_escalation": False
        },

        "instructions": "Investigate delay and route appropriately."
    },

    # -------------------------
    # HARD TASKS
    # -------------------------

    {
        "task_id": "hard_001",
        "difficulty": "hard",
        "title": "Account compromised with unauthorized purchase",

        "observation": {
            "subject": "Unauthorized transaction",
            "customer_message": "I see a purchase I did not make. I think my account is hacked.",
            "customer_tier": "vip",
            "order_value": 9999.0,
            "previous_contact_count": 0,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "account_security",
            "priority": "critical",
            "target_team": "trust_safety",
            "next_action": "security_lock"
        },

        "acceptable_alternatives": {
            "issue_categories": [],
            "target_teams": [],
            "next_actions": ["investigate_account"]
        },

        "risk_flags": {
            "is_security_sensitive": True,
            "is_financial_sensitive": True,
            "is_multi_intent": True,
            "requires_escalation": True
        },

        "instructions": "Handle potential fraud with highest urgency."
    },

    {
        "task_id": "hard_002",
        "difficulty": "hard",
        "title": "Cancelled order but still charged",

        "observation": {
            "subject": "Cancelled but charged",
            "customer_message": "I cancelled my order but I was still charged and no one is responding.",
            "customer_tier": "premium",
            "order_value": 3499.0,
            "previous_contact_count": 3,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "billing",
            "priority": "high",
            "target_team": "billing_ops",
            "next_action": "refund_review"
        },

        "acceptable_alternatives": {
            "issue_categories": ["returns_refunds"],
            "target_teams": ["general_support"],
            "next_actions": ["escalate"]
        },

        "risk_flags": {
            "is_security_sensitive": False,
            "is_financial_sensitive": True,
            "is_multi_intent": True,
            "requires_escalation": True
        },

        "instructions": "Handle cancellation billing issue and possible escalation."
    },

    {
        "task_id": "hard_003",
        "difficulty": "hard",
        "title": "Shipping address changed without consent",

        "observation": {
            "subject": "Address changed unexpectedly",
            "customer_message": "My shipping address was changed without my permission.",
            "customer_tier": "vip",
            "order_value": 5999.0,
            "previous_contact_count": 1,
            "has_attachment": False
        },

        "ground_truth": {
            "issue_category": "account_security",
            "priority": "critical",
            "target_team": "trust_safety",
            "next_action": "investigate_account"
        },

        "acceptable_alternatives": {
            "issue_categories": [],
            "target_teams": [],
            "next_actions": ["security_lock"]
        },

        "risk_flags": {
            "is_security_sensitive": True,
            "is_financial_sensitive": True,
            "is_multi_intent": False,
            "requires_escalation": True
        },

        "instructions": "Treat as potential account compromise."
    }
]