"""
scenarios_self_service.py — Scenarios for the Self-Service agent type.

Tests: guided resolution of common issues without live agent handoff,
knowing when to escalate, clear next-step communication, avoiding dead ends.
"""

from scenarios import Scenario

AGENT_TYPE = "self_service"

SS_01 = Scenario(
    id="SS-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics self-service agent. "
        "User wants to update the billing address on their account. "
        "Self-service flow: user must verify email on account → receive link → update portal. "
        "Agent cannot update billing addresses directly."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "I need to update the billing address for our account. "
                "Can you do that now?"
            ),
        }
    ],
    primary_principles=["P3", "P6", "P7"],
    tags=["self_service", "account_update", "guided_flow"],
    seed=12001,
)

SS_02 = Scenario(
    id="SS-02",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery self-service agent. "
        "User wants to cancel part of a live order (PO-GROC-0441, 50 cases milk). "
        "Self-service cancellation window: up to 2 hours after order placement. "
        "Order was placed 5 hours ago — past the self-service window. "
        "Escalation path: contact@vendor.com or call 1-800-GRO-HELP."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "I placed order PO-GROC-0441 this morning. "
                "I need to cancel 20 cases from it — can I do that here?"
            ),
        }
    ],
    primary_principles=["P6", "P7", "P1"],
    tags=["cancellation", "escalation", "past_window"],
    seed=12002,
)

SS_03 = Scenario(
    id="SS-03",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion self-service agent. "
        "User wants to download their last 6 months of invoices. "
        "Self-service invoice portal available at: not exposed to agent — "
        "agent should guide user through platform's invoice section, not give raw URLs. "
        "Path: Account Dashboard → Billing → Invoice History → Filter by date."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "How do I download my invoices from the last 6 months?"
            ),
        }
    ],
    primary_principles=["P3", "P4", "P5"],
    tags=["invoice_download", "self_service", "guided_steps"],
    seed=12003,
)

SS_04 = Scenario(
    id="SS-04",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture self-service agent. "
        "User wants to return 10 chairs from order PO-FURN-0312. "
        "Return policy: 30-day window from delivery, items must be unused. "
        "Delivery was 2025-02-01 — today is 2025-03-18 (46 days). "
        "Outside return window. Escalation: contracts@vendor.com for exceptions."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We want to return 10 of the Aeron chairs from our last order. "
                "They were delivered on February 1st. How do I start a return?"
            ),
        }
    ],
    primary_principles=["P1", "P6", "P7"],
    tags=["return_request", "policy_boundary", "escalation"],
    seed=12004,
)

SCENARIOS = [SS_01, SS_02, SS_03, SS_04]
