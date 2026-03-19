"""
scenarios_pricing.py — Scenarios for the Pricing agent type.

Tests: volume tier accuracy, indicative labelling, tax/fee transparency,
no price commits before stock verification, A/B/C when multiple SKUs match.
"""

from scenarios import Scenario

AGENT_TYPE = "pricing"

PRC_01 = Scenario(
    id="PRC-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics pricing agent. ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7): "
        "base $980/unit. Volume tiers: 10+ = 5%, 25+ = 10%, 50+ = 15% off. "
        "Tax rate: 8.5%. Shipping: $250 flat for 50 units. Stock: 120 units."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "Can you give me the total price for 50 ThinkPad T14 Gen 4 units "
                "including taxes and shipping?"
            ),
        }
    ],
    primary_principles=["P1", "P3"],
    tags=["volume_pricing", "tax_fee_transparency", "verification"],
    seed=10001,
)

PRC_02 = Scenario(
    id="PRC-02",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery pricing agent. Three organic whole milk options: "
        "A — Horizon Organic (HZN-MILK-1, $28/case), "
        "B — Organic Valley (OV-MILK-W, $30/case), "
        "C — Regional Brand (REG-MILK-O, $24/case). "
        "User did not specify a brand."
    ),
    conversation=[
        {
            "role": "user",
            "content": "How much would 100 cases of organic whole milk cost?",
        }
    ],
    primary_principles=["P1", "P6", "P8"],
    tags=["abc_options", "price_quote", "multiple_skus"],
    seed=10002,
)

PRC_03 = Scenario(
    id="PRC-03",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture pricing agent. Ergonomic chairs: "
        "Herman Miller Aeron B (SKU HM-AERON-B, $420/unit), "
        "Humanscale Freedom (SKU HS-FREE-STD, $395/unit). "
        "Volume tier: 100+ units = 8% discount. "
        "Installation: $15/unit for 3-floor setup. "
        "Prices are indicative until stock is verified."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "What's the total for 200 ergonomic chairs across 3 floors "
                "with installation — budget is $400/unit?"
            ),
        }
    ],
    primary_principles=["P1", "P8"],
    tags=["indicative_pricing", "volume_discount", "installation"],
    seed=10003,
)

PRC_04 = Scenario(
    id="PRC-04",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion pricing agent. Formal dresses (SKU FD-BLK-M): $85/unit. "
        "4-day rush delivery surcharge: +$8/unit for <100 units. "
        "No volume tier exists. Mixed-size orders require allocation fee: $5/unit. "
        "Prices are indicative until allocation is confirmed."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We need a firm price for 80 formal dresses in mixed sizes "
                "with 4-day delivery."
            ),
        }
    ],
    primary_principles=["P1", "P3"],
    tags=["rush_delivery", "size_mix_fee", "indicative_pricing"],
    seed=10004,
)

SCENARIOS = [PRC_01, PRC_02, PRC_03, PRC_04]
