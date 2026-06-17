from __future__ import annotations

import json
from pathlib import Path

from core_lite.transition_table.formalism_refs import validate_policy_formalism_linkage


def test_policy_links_stage_32_to_34_formalism_refs():
    policy = json.loads(Path("core_lite/transition_table/policy.json").read_text(encoding="utf-8"))
    status = validate_policy_formalism_linkage(policy)
    assert status.ok, status.errors


def test_policy_preserves_required_decision_regions():
    policy = json.loads(Path("core_lite/transition_table/policy.json").read_text(encoding="utf-8"))
    regions = set(policy["decision_regions"].keys())
    assert {"ALLOW", "DENY", "SANDBOX", "REVIEW", "FAIL_CLOSED", "QUARANTINE"}.issubset(regions)


def test_policy_preserves_required_boundary_metrics():
    policy = json.loads(Path("core_lite/transition_table/policy.json").read_text(encoding="utf-8"))
    metrics = set(policy["boundary_metrics"].keys())
    assert {"d_A", "delta_R", "delta_P", "delta_U", "delta_O", "delta_C"}.issubset(metrics)
    assert "d_bnd_A" in metrics or "d_boundary_A" in metrics
