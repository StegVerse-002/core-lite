# Transition Table Gate Tests

Decision: `ALLOW`
Success: `true`
Runner mode: `script_style_tests_not_pytest_collection`
Report: `reports/current/transition_table_gate_test_report.json`
Receipt: `receipts/current/transition_table_gate_test_receipt.jsonl`

## Commands

### `/opt/hostedtoolcache/Python/3.11.15/x64/bin/python tests/test_transition_table_resolver.py`

Return code: `0`
Success: `true`

stdout tail:

```text
Tests: 14/14 passed — PASS
  [PASS] valid_candidate_decision: decision=ALLOW_CANDIDATE_ONLY
  [PASS] valid_candidate_disposition: disposition=CANDIDATE_ACCEPTED_FOR_COMPARISON
  [PASS] valid_candidate_no_errors: errors=[]
  [PASS] missing_transition_fail_closed: decision=FAIL_CLOSED
  [PASS] unknown_class_fail_closed: decision=FAIL_CLOSED, errors=["FAIL_CLOSED: transition_class 'quantum_leap' is unknown (known: ['candidate', 'evidence', 'execution', 'install', 'repair'])"]
  [PASS] missing_task_hash_has_errors: errors=["missing required field 'task_hash' for transition_class 'candidate'"]
  [PASS] missing_task_hash_high_delta_P: delta_P=0.5
  [PASS] authority_mismatch_has_errors: errors=["authority_class 'scoped_repo_write' not allowed for 'candidate' (allowed: ['candidate_evidence_only'])"]
  [PASS] state_effect_mismatch_has_errors: errors=["state_effect 'code_state' not allowed for 'candidate' (allowed: ['evidence_state'])"]
  [PASS] install_decision_allow: decision=ALLOW
  [PASS] install_installs_code: installs_code=True
  [PASS] execution_no_authority_high_delta_U: delta_U=0.9, decision=FAIL_CLOSED
  [PASS] all_coordinate_keys_present: missing=set()
  [PASS] allows_candidate_processing: decision=ALLOW_CANDIDATE_ONLY, installs_code=False

```

stderr tail:

```text

```

### `/opt/hostedtoolcache/Python/3.11.15/x64/bin/python tests/test_bundle_ingest_cge_transition_gate.py`

Return code: `0`
Success: `true`

stdout tail:

```text
Tests: 12/12 passed — PASS
  [PASS] candidate_decision_allow_candidate_only: decision=ALLOW_CANDIDATE_ONLY
  [PASS] candidate_disposition_accepted: disposition=CANDIDATE_ACCEPTED_FOR_COMPARISON
  [PASS] candidate_no_code_install: installs_code=False
  [PASS] candidate_receipt_hash_present: receipt_hash=sha256:3dfbe8f0a8b52...
  [PASS] no_manifest_fail_closed: decision=FAIL_CLOSED
  [PASS] install_decision_allow: decision=ALLOW
  [PASS] install_installs_code: installs_code=True
  [PASS] transition_table_receipt_written: path=/tmp/tmptgei10ej/receipts/current/transition_table_receipt.jsonl
  [PASS] cge_receipt_written: path=/tmp/tmptgei10ej/receipts/current/cge_admissibility_receipt.jsonl
  [PASS] report_written: path=/tmp/tmptgei10ej/reports/current/transition_table_report.json
  [PASS] dry_run_preserved: dry_run=True
  [PASS] coordinates_present: keys=['delta_C', 'delta_R', 'delta_P', 'delta_U', 'delta_O', 'd_boundary_A', 'd_A']

```

stderr tail:

```text

```

