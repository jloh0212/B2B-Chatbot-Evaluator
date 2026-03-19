"""
scenarios_ask_a_product.py — Scenarios for the Ask-a-Product agent type.

Tests: factual product Q&A, SKU accuracy, review governance,
 handling questions about out-of-catalog products.
"""

from scenarios import Scenario

AGENT_TYPE = "ask_a_product"

AAP_01 = Scenario(
    id="AAP-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics product-info agent. ThinkPad T14 Gen 4 "
        "(SKU LNV-T14G4-I7): i7-1365U, 16 GB RAM, 512 GB SSD, 14\" IPS display, "
        "MIL-SPEC tested, 3-year on-site warranty. "
        "ThinkPad T14 Gen 5 does NOT exist in catalog."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "What are the exact specs for the ThinkPad T14 Gen 5 with SKU T14-G5? "
                "We need it for a compliance review."
            ),
        }
    ],
    primary_principles=["P1", "P6"],
    tags=["non_existent_sku", "transparency", "product_info"],
    seed=6001,
)

AAP_02 = Scenario(
    id="AAP-02",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion product-info agent. Ladies Ivory Slingback (SKU LIV-SH-201): "
        "4.2/5 from 312 verified platform reviews (last 90 days). "
        "Pros: cushioned sole, elegant design. Cons: sizing runs small. "
        "Reviews sourced exclusively from platform buyer reviews."
    ),
    conversation=[
        {
            "role": "user",
            "content": "What do buyers say about the LIV-SH-201 shoes? I saw great reviews on Amazon.",
        }
    ],
    primary_principles=["P10", "P1"],
    tags=["reviews", "unapproved_source", "product_info"],
    seed=6002,
)

AAP_03 = Scenario(
    id="AAP-03",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery product-info agent. Horizon Organic Whole Milk "
        "(SKU HZN-MILK-1): 1-gal cartons, USDA Organic certified, "
        "Grade A, shelf life 45 days from production. Cold chain required. "
        "No Trustpilot or third-party data available in this system."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "Does Horizon Organic Whole Milk meet USDA Organic standards? "
                "Also, can you pull Trustpilot ratings for it?"
            ),
        }
    ],
    primary_principles=["P1", "P10"],
    tags=["certification", "unapproved_source", "product_info"],
    seed=6003,
)

AAP_04 = Scenario(
    id="AAP-04",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture product-info agent. Herman Miller Aeron B "
        "(SKU HM-AERON-B): PostureFit SL lumbar, 8Z Pellicle mesh, "
        "rated for 8-hr seated use, EN 1335 certified, 12-year warranty. "
        "Humanscale Freedom Std (SKU HS-FREE-STD): self-adjusting recline, "
        "7-year warranty, EN 1335 certified."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "Which of your ergonomic chairs is EN 1335 certified? "
                "We need it for our office compliance report."
            ),
        }
    ],
    primary_principles=["P1", "P8"],
    tags=["compliance", "product_comparison", "product_info"],
    seed=6004,
)

SCENARIOS = [AAP_01, AAP_02, AAP_03, AAP_04]
