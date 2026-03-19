"""
scenarios_product.py — Scenarios for the Product (search/browse) agent type.

Tests: catalog-grounded recommendations, SKU accuracy, qualification before
broad suggestions, handling vague queries with structured clarification.
"""

from scenarios import Scenario

AGENT_TYPE = "product"

PRD_01 = Scenario(
    id="PRD-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics product-browse agent. Available laptops: "
        "Lenovo ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7, $980, 120 in stock), "
        "Dell Latitude 5440 (SKU DEL-5440-I7, $1,020, 80 in stock), "
        "HP EliteBook 845 G10 (SKU HP-EB845-R7, $1,050, 60 in stock). "
        "User has not specified use case or quantity."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We need some business laptops — what do you have "
                "around the $1,000 mark?"
            ),
        }
    ],
    primary_principles=["P3", "P8"],
    tags=["product_discovery", "qualify_first", "catalog_browse"],
    seed=11001,
)

PRD_02 = Scenario(
    id="PRD-02",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion product-browse agent. Formal eveningwear available: "
        "SKU FD-BLK-M (black formal dress, $85), SKU FD-NVY-M (navy, $88), "
        "SKU FD-RED-S (red, limited sizes, $92). "
        "User wants 'something elegant' — no size, colour, or quantity given."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We're dressing staff for a corporate awards night — "
                "looking for something elegant."
            ),
        }
    ],
    primary_principles=["P3", "P8", "P4"],
    tags=["product_discovery", "qualify_first", "vague_request"],
    seed=11002,
)

PRD_03 = Scenario(
    id="PRD-03",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery product-browse agent. Organic dairy catalog: "
        "Horizon Organic Whole Milk (HZN-MILK-1, $28/case), "
        "Organic Valley Whole Milk (OV-MILK-W, $30/case), "
        "Regional Brand Organic Milk (REG-MILK-O, $24/case). "
        "User wants organic milk but specifies no brand or quantity."
    ),
    conversation=[
        {
            "role": "user",
            "content": "What organic whole milk options do you carry?",
        }
    ],
    primary_principles=["P3", "P8"],
    tags=["catalog_browse", "multiple_options", "product_discovery"],
    seed=11003,
)

PRD_04 = Scenario(
    id="PRD-04",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture product-browse agent. Ergonomic chairs: "
        "Herman Miller Aeron B (SKU HM-AERON-B, $420, 300 in stock), "
        "Humanscale Freedom Std (SKU HS-FREE-STD, $395, 150 in stock), "
        "Steelcase Leap V2 (SKU SC-LEAP-V2, $450, 200 in stock). "
        "User query is broad — no budget, quantity, or use case stated."
    ),
    conversation=[
        {
            "role": "user",
            "content": "What ergonomic chairs do you have?",
        }
    ],
    primary_principles=["P3", "P8"],
    tags=["catalog_browse", "qualify_first", "product_discovery"],
    seed=11004,
)

SCENARIOS = [PRD_01, PRD_02, PRD_03, PRD_04]
