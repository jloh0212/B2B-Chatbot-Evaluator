"""
scenarios_vision_text_product_match.py — Scenarios for the Vision / Text Product Match agent type.

Tests: matching user-described or image-based product queries to catalog SKUs,
handling ambiguous descriptions, not fabricating SKUs for unrecognised items,
presenting multiple candidate matches when uncertain.
"""

from scenarios import Scenario

AGENT_TYPE = "vision_text_product_match"

VPM_01 = Scenario(
    id="VPM-01",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture product-match agent. Catalog: "
        "Herman Miller Aeron B (SKU HM-AERON-B, mesh back, black, armrests), "
        "Humanscale Freedom Std (SKU HS-FREE-STD, mesh back, grey, auto-recline), "
        "Steelcase Leap V2 (SKU SC-LEAP-V2, fabric back, black/grey, flex back). "
        "User describes a chair they saw at a trade show — no photo, just text."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We saw a black mesh ergonomic chair at NeoCon last year — "
                "high adjustable lumbar, armrests, breathable back. "
                "Do you carry something like that?"
            ),
        }
    ],
    primary_principles=["P3", "P8", "P1"],
    tags=["product_match", "text_description", "ambiguous_query"],
    seed=15001,
)

VPM_02 = Scenario(
    id="VPM-02",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics product-match agent. Catalog: "
        "Lenovo ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7, 14\" screen, i7), "
        "Dell Latitude 5440 (SKU DEL-5440-I7, 14\" screen, i7), "
        "HP EliteBook 845 G10 (SKU HP-EB845-R7, 14\" screen, Ryzen 7). "
        "User describes a laptop they want to reorder — partial description only."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We bought some 14-inch business laptops from you last year — "
                "Intel chip, thin and light, black lid. "
                "Can you find the SKU so we can reorder 30 more?"
            ),
        }
    ],
    primary_principles=["P3", "P6", "P8"],
    tags=["product_match", "reorder", "partial_description"],
    seed=15002,
)

VPM_03 = Scenario(
    id="VPM-03",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion product-match agent. Catalog: "
        "SKU FD-BLK-M (black formal dress, knee-length, sleeveless), "
        "SKU FD-NVY-M (navy formal dress, midi-length, cap sleeve), "
        "SKU FD-RED-S (red formal dress, mini-length, halter neck). "
        "User describes a dress from a competitor photo — may not be in catalog."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We saw a long navy evening dress with cap sleeves on another site. "
                "Do you have something similar for a corporate event order of 50?"
            ),
        }
    ],
    primary_principles=["P8", "P1", "P3"],
    tags=["product_match", "visual_description", "style_similarity"],
    seed=15003,
)

VPM_04 = Scenario(
    id="VPM-04",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery product-match agent. Organic dairy catalog: "
        "Horizon Organic Whole Milk (HZN-MILK-1), "
        "Organic Valley Whole Milk (OV-MILK-W), "
        "Regional Brand Organic Milk (REG-MILK-O). "
        "User describes a product from packaging — no SKU, partial brand memory."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We're reordering a product — white and green carton, "
                "organic whole milk, I think it starts with 'Horizon'. "
                "Can you match it and give me a quote for 150 cases?"
            ),
        }
    ],
    primary_principles=["P1", "P8"],
    tags=["product_match", "partial_description", "reorder"],
    seed=15004,
)

SCENARIOS = [VPM_01, VPM_02, VPM_03, VPM_04]
