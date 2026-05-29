"""
core_lite/transition_table — StegVerse-002
Transition Table resolution layer.

Usage:
    from core_lite.transition_table import TransitionTableResolver, TransitionAttributes

    resolver = TransitionTableResolver()
    decision = resolver.resolve(manifest, bundle_hash=bundle_hash, entity=entity, stage=stage)

    if decision.is_fail_closed():
        # quarantine
    elif decision.allows_candidate_processing():
        # route to comparison/synthesis
    elif decision.allows_code_install():
        # proceed to CGE then install
"""
from .attributes import TransitionAttributes
from .resolver import TransitionTableResolver, TransitionDecision

__all__ = ["TransitionTableResolver", "TransitionAttributes", "TransitionDecision"]
