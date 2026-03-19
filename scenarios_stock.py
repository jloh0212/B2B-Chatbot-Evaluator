"""
scenarios_stock.py — Scenarios for the Stock Check agent type.

Tests: accurate stock reporting, handling out-of-stock gracefully,
multi-store allocation, no commitment before stock is verified.
"""

from scenarios import Scenario

AGENT_TYPE = "stock"

STK_01 = Scenario(
    id="STK-01",
    industry="Electronics",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B electronics stock agent. "
        "Lenovo ThinkPad T14 Gen 4 (SKU LNV-T14G4-I7): 120 units in stock. "
        "Dell Latitude 5440 (SKU DEL-5440-I7): 80 units in stock. "
        "HP EliteBook 845 G10 (SKU HP-EB845-R7): 0 units — OUT OF STOCK, "
        "restock ETA 2025-04-01."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "Can you check stock for ThinkPad T14 Gen 4, Dell Latitude 5440, "
                "and HP EliteBook 845 G10? We need 50 of each."
            ),
        }
    ],
    primary_principles=["P1", "P6"],
    tags=["stock_check", "out_of_stock", "multi_sku"],
    seed=13001,
)

STK_02 = Scenario(
    id="STK-02",
    industry="Grocery",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B grocery stock agent. "
        "Horizon Organic Whole Milk (SKU HZN-MILK-1): 350 cases total, "
        "but regional allocation required for 8-store distribution. "
        "Max per warehouse: 50 cases. "
        "Agent must NOT confirm availability for 200 cases without allocation check."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We need 200 cases of HZN-MILK-1 split across 8 stores. "
                "Is stock available?"
            ),
        }
    ],
    primary_principles=["P1", "P5"],
    tags=["stock_check", "multi_store", "allocation"],
    seed=13002,
)

STK_03 = Scenario(
    id="STK-03",
    industry="Furniture",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B furniture stock agent. "
        "Herman Miller Aeron B (SKU HM-AERON-B): 300 units. "
        "Humanscale Freedom Std (SKU HS-FREE-STD): 150 units. "
        "Steelcase Leap V2 (SKU SC-LEAP-V2): 12 units — LOW STOCK. "
        "User asking about all three for a 200-unit order."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We need 200 ergonomic chairs. "
                "Can you check which ones are fully in stock — Aeron B, "
                "Humanscale Freedom, or Steelcase Leap V2?"
            ),
        }
    ],
    primary_principles=["P1", "P8"],
    tags=["stock_check", "low_stock", "multi_sku"],
    seed=13003,
)

STK_04 = Scenario(
    id="STK-04",
    industry="Fashion",
    agent_type=AGENT_TYPE,
    agent_context=(
        "B2B fashion stock agent. "
        "Formal Dress FD-BLK-M: 200 units total, but size breakdown: "
        "XS=10, S=30, M=80, L=50, XL=20, XXL=10. "
        "User needs 80 dresses in mixed sizes — feasibility depends on size mix."
    ),
    conversation=[
        {
            "role": "user",
            "content": (
                "We need 80 formal dresses (SKU FD-BLK-M) in mixed sizes. "
                "Is this in stock?"
            ),
        }
    ],
    primary_principles=["P1", "P3"],
    tags=["stock_check", "size_allocation", "mixed_sizes"],
    seed=13004,
)

SCENARIOS = [STK_01, STK_02, STK_03, STK_04]
