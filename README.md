# Customer Support Triage OpenEnv

A deterministic, real-world environment for evaluating AI agents on customer support triage decisions.

---

# Overview

This OpenEnv environment simulates a customer support system where an agent must:

- Identify the issue type
- Assign priority
- Route to the correct team
- Choose the next action

Each episode represents a single customer case and is evaluated in one step.

---

# Action Format

The agent must return:

```json
{
  "issue_category": "...",
  "priority": "...",
  "target_team": "...",
  "next_action": "...",
  "reason": "..."
}
```

---

# Environment

- Single-step, deterministic environment
- Each task = one customer case
- One action equals immediate evaluation

# Endpoints

- `POST /reset`
- `POST /step`
- `GET /tasks`

---

# Tasks

- 9 tasks across 3 difficulty levels:

  - Easy (clear issues)
  - Medium (ambiguous cases)
  - Hard (security / fraud scenarios)

---

# Reward

Deterministic rule-based scoring:

| Component      | Weight |
| -------------- | ------ |
| Issue Category | 0.30   |
| Priority       | 0.20   |
| Target Team    | 0.20   |
| Next Action    | 0.30   |

- Partial credit supported
- Penalties for unsafe decisions
- Final score in [0.0, 1.0]

---

# Run Locally

```bash
uv sync
uv run uvicorn server.app:app --reload
```

Test:

```bash
curl http://localhost:8000/tasks
```

---

# Baseline

```bash
uv run inference.py
```

Runs all tasks and outputs reproducible scores.

---

# Deployment

```bash
openenv push --repo-id <your-username>/customer-support-openenv
```

---

# Author - Kishore Choudhury

Meta x PyTorch Hackathon (Scaler)
