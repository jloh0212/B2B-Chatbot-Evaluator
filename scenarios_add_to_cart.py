"""
scenarios_add_to_cart.py — Scenarios for the Add-to-Cart agent type.

Tests: context retention after browsing, confirmation before acting,
quantity deduplication, clear summarisation of what's being added.
"""

from scenarios import Scenario

AGENT_TYPE = "add_to_cart"

ATC_01 = Scenario(
    id="ATC-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics add-to-cart agent. Prior turn: agent showed Lenovo ThinkPad T14 Gen 4 "
        "(SKU LNV-T14G4-I7, $980/unit, 120 in stock) and Dell Latitude 5440 "
        "(SKU DEL-5440-I7, $1,020/unit, 80 in stock). "
        "User now says 'Add the Lenovo, 25 units' without restating the SKU."
    ),
    conversation=[
        {"role": "user", "content": "Show me business laptops around $1,000."},
        {
            "role": "assistant",
            "content": (
                "Two verified options:\n"
                "- Lenovo ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7) — best for mobile teams; $980/unit; 120 in stock\n"
                "- Dell Latitude 5440 (SKU DEL-5440-I7) — best for battery life; $1,020/unit; 80 in stock\n"
                "Tell me your quantity and I'll confirm tiered pricing."
            ),
        },
        {"role": "user", "content": "Add the Lenovo, 25 units."},
    ],
    primary_principles=["P2", "P5"],
    tags=["multi_turn", "context_retention", "cart_action"],
    seed=5001,
)

ATC_02 = Scenario(
    id="ATC-02",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery add-to-cart agent. Prior conversation: agent recommended "
        "Horizon Organic Whole Milk (SKU HZN-MILK-1, $28/case). "
        "User now says 'Add that — 120 cases' using a pronoun."
    ),
    conversation=[
        {"role": "user", "content": "What organic whole milk do you recommend?"},
        {
            "role": "assistant",
            "content": (
                "Top pick: Horizon Organic Whole Milk (SKU HZN-MILK-1) — "
                "best for national brand coverage; $28/case.\n"
                "What quantity and delivery window do you need?"
            ),
        },
        {"role": "user", "content": "Add that — 120 cases."},
    ],
    primary_principles=["P2", "P5"],
    tags=["pronoun_resolution", "context_retention", "cart_action"],
    seed=5002,
)

ATC_03 = Scenario(
    id="ATC-03",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture add-to-cart agent. Cart state: Herman Miller Aeron B "
        "(SKU HM-AERON-B) was added twice — 10 units then 15 units. "
        "System should consolidate to 25 units, not create two line items."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "I added Herman Miller Aeron chairs twice — 10 units first, "
                "then 15 units just now. Can you fix the duplicate in my cart?"
            ),
        }
    ],
    primary_principles=["P5", "P2"],
    tags=["cart_dedup", "multi_action", "confirmation"],
    seed=5003,
)

ATC_04 = Scenario(
    id="ATC-04",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion add-to-cart agent. Formal dress available: "
        "SKU FD-BLK-M (black, mixed sizes), stock 200, $85/unit. "
        "User wants to add to cart without specifying size split."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "Add 80 formal dresses to my cart — we need mixed sizes "
                "for an awards gala."
            ),
        }
    ],
    primary_principles=["P1", "P3", "P5"],
    tags=["size_ambiguity", "confirmation_gate", "cart_action"],
    seed=5004,
)

SCENARIOS = [ATC_01, ATC_02, ATC_03, ATC_04]
