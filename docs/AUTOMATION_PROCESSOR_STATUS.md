# Automation Processor Status

This pass added a repo-local automation request processor.

## Command

```text
python tools/process_automation_requests.py
```

## Request Source

```text
automation/stegguardian-workflow-install-request.json
```

## Receipt Output

```text
receipts/automation-processing-receipt.json
```

## Purpose

The processor consumes the existing install request and performs the remaining file-promotion action locally when invoked by an ecosystem runner.

## Next Step

Add the processor command to the ecosystem bootstrap path before unified validation.
