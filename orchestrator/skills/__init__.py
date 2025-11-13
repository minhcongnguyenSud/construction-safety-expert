"""
Construction Safety Skills Package

Specialized skills for handling different categories of construction hazards.

Available Skills:
- FallHazardSkill: Falls, scaffolds, ladders, MEWPs, fall protection
- ElectricalHazardSkill: Electrical hazards, LOTO, power lines, arc flash
- StruckByHazardSkill: Mobile equipment, traffic control, falling objects
- GeneralSafetySkill: All other hazards (excavation, confined spaces, etc.)

Usage:
    from orchestrator.skills import FallHazardSkill

    skill = FallHazardSkill(llm)
    result = skill.process("What are fall protection requirements?")
"""

from .fall_hazard import FallHazardSkill
from .electrical_hazard import ElectricalHazardSkill
from .struckby_hazard import StruckByHazardSkill
from .general_safety import GeneralSafetySkill

__all__ = [
    'FallHazardSkill',
    'ElectricalHazardSkill',
    'StruckByHazardSkill',
    'GeneralSafetySkill'
]
