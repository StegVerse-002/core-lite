from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_STAGE_NAMES = {
    "Stage32-AdmissibilitySpaceCoordinates",
    "Stage33-TransitionGraphGeometry",
    "Stage34-RepairNearestAdmissible",
}
REQUIRED_REPO = "Data-Continuation/formalism-tests"
REQUIRED_DECISION_REGIONS = {"ALLOW", "DENY", "SANDBOX", "REVIEW", "FAIL_CLOSED", "QUARANTINE"}
REQUIRED_BOUNDARY_METRICS = {"d_A", "delta_R", "delta_P", "delta_U", "delta_O", "delta_C"}


@dataclass(frozen=True)
class FormalismLinkageStatus:
    ok: bool
    errors: list[str]
    warnings: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings}


def validate_policy_formalism_linkage(policy: dict[str, Any]) -> FormalismLinkageStatus:
    errors: list[str] = []
    warnings: list[str] = []

    refs = policy.get("formalism_refs", [])
    if not isinstance(refs, list) or not refs:
        errors.append("formalism_refs_missing")
        refs = []

    by_name = {ref.get("formalism"): ref for ref in refs if isinstance(ref, dict)}
    for name in sorted(REQUIRED_STAGE_NAMES):
        ref = by_name.get(name)
        if not ref:
            errors.append(f"formalism_ref_missing:{name}")
            continue
        if ref.get("repo") != REQUIRED_REPO:
            errors.append(f"formalism_ref_repo_mismatch:{name}")
        if not ref.get("artifact"):
            errors.append(f"formalism_ref_artifact_missing:{name}")
        if not ref.get("report_path"):
            errors.append(f"formalism_ref_report_path_missing:{name}")

    regions = set((policy.get("decision_regions") or {}).keys())
    missing_regions = sorted(REQUIRED_DECISION_REGIONS - regions)
    if missing_regions:
        errors.append("decision_regions_missing:" + ",".join(missing_regions))

    metrics = set((policy.get("boundary_metrics") or {}).keys())
    missing_metrics = sorted(REQUIRED_BOUNDARY_METRICS - metrics)
    if missing_metrics:
        errors.append("boundary_metrics_missing:" + ",".join(missing_metrics))

    if "d_bnd_A" not in metrics and "d_boundary_A" not in metrics:
        errors.append("boundary_metric_missing:d_boundary_A_or_d_bnd_A")

    if policy.get("schema") != "stegverse.transition_table_policy.v1":
        errors.append("policy_schema_mismatch")

    if policy.get("stage") not in {"SV002-M11", "SV002-M12", "SV002-M13", "SV002-M14"}:
        warnings.append(f"unexpected_policy_stage:{policy.get('stage')}")

    return FormalismLinkageStatus(ok=not errors, errors=errors, warnings=warnings)
