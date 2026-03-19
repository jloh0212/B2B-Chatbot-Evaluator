"""
scenarios_complementary_product.py — Scenarios for the Complementary Product agent type.

Tests: relevant upsell / cross-sell recommendations, staying within catalog,
qualification before recommending extras, not overwhelming with options.
"""

from scenarios import Scenario

AGENT_TYPE = "complementary_product"

CMP_01 = Scenario(
    id="CMP-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics complementary-product agent. Primary purchase: "
        "50 × Lenovo ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7). "
        "Available accessories: Lenovo USB-C Dock (SKU LNV-DOCK-U3, $129/unit), "
        "Lenovo Active Pen (SKU LNV-PEN-A2, $49/unit), "
        "Kensington Lock (SKU KEN-LOCK-C, $18/unit). "
        "No third-party accessories unless user asks."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We've confirmed 50 ThinkPad T14s. "
                "What accessories would you recommend for a remote sales team?"
            ),
        }
    ],
    primary_principles=["P3", "P8", "P2"],
    tags=["upsell", "accessory_recommendation", "qualification"],
    seed=7001,
)

CMP_02 = Scenario(
    id="CMP-02",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion complementary-product agent. Primary order: "
        "80 × formal dresses (SKU FD-BLK-M). "
        "Matching accessories: Ladies Ivory Slingback (SKU LIV-SH-201, $55/unit), "
        "Black clutch bag (SKU CLT-BLK-S, $32/unit). "
        "Do not recommend non-catalog items."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We've ordered 80 formal dresses for the gala. "
                "Any matching accessories you'd suggest to complete the look?"
            ),
        }
    ],
    primary_principles=["P3", "P8"],
    tags=["cross_sell", "accessory_recommendation", "fashion"],
    seed=7002,
)

CMP_03 = Scenario(
    id="CMP-03",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery complementary-product agent. Primary order: "
        "200 cases Horizon Organic Whole Milk (SKU HZN-MILK-1). "
        "Complementary: Horizon Organic Cream (SKU HZN-CRM-1, $34/case), "
        "Organic Valley Butter (SKU OV-BTR-L, $26/case). "
        "Cold-chain required for all items."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We've got our milk order sorted. Any other organic dairy "
                "that pairs well and ships on the same cold-chain delivery?"
            ),
        }
    ],
    primary_principles=["P3", "P8", "P1"],
    tags=["cross_sell", "cold_chain", "complementary"],
    seed=7003,
)

CMP_04 = Scenario(
    id="CMP-04",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture complementary-product agent. Primary order: "
        "200 × Herman Miller Aeron B (SKU HM-AERON-B). "
        "Complementary: Herman Miller Laptop Arm (SKU HM-ARM-L, $85/unit), "
        "Humanscale M10 Monitor Arm (SKU HS-M10-BLK, $120/unit), "
        "Cable management tray (SKU CMG-TRY-BLK, $22/unit). "
        "User budget: ~$50/unit for accessories."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "200 Aeron chairs confirmed. We also want to set up the desks properly — "
                "any accessories to complement the chairs within $50/unit?"
            ),
        }
    ],
    primary_principles=["P3", "P8", "P1"],
    tags=["upsell", "budget_filter", "complementary"],
    seed=7004,
)

SCENARIOS = [CMP_01, CMP_02, CMP_03, CMP_04]
