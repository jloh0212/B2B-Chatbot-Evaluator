"""
rules/__init__.py — Import all rule check functions for convenience.
"""
from .p1_transparency import check as check_p1
from .p2_personalization import check as check_p2
from .p3_efficiency import check as check_p3
from .p4_communication import check as check_p4
from .p5_multiaction import check as check_p5
from .p6_error_handling import check as check_p6
from .p7_handoff import check as check_p7
from .p8_recommendations import check as check_p8
from .p9_security import check as check_p9
from .p10_feedback import check as check_p10

__all__ = [
    "check_p1", "check_p2", "check_p3", "check_p4", "check_p5",
    "check_p6", "check_p7", "check_p8", "check_p9", "check_p10",
]
