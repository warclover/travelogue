"""AI Capability Platform (ACP) · orchestration layer over ``travelogue.llm``.

See ``docs/PRD-AI-CAPABILITY-PLATFORM-V1.md``. This package must not import
upward into curation / layout_engine / cover_engine / services / web.
"""

from __future__ import annotations

from travelogue.ai.budget import TripLlmBudget
from travelogue.ai.gate import GateDecision, check_gate
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call

__all__ = [
    "AgentCallRecord",
    "GateDecision",
    "TripLlmBudget",
    "check_gate",
    "record_agent_call",
]
