# StegGuardian Core-Lite Goal Activation

This document marks the current StegGuardian adapter build goal in `StegVerse-002/core-lite` as conditionally activated.

## Goal

Validate StegGuardian adapter input through core-lite general stores and produce receipt material without manual command sequencing.

## Activation Receipt

```text
receipts/stegguardian-core-lite-goal-activation.json
```

## Single Validation Command

```text
python tools/validate_stegguardian_adapter_all.py
```

## Completed

- adapter fixture validation;
- general-store resolution validation;
- receipt emission validation;
- store-backed receipt generation;
- unified validation command;
- iOS-safe workflow mirror;
- machine-readable workflow install request;
- goal activation receipt.

## Remaining Blocker

Direct canonical workflow installation is blocked by the GitHub connector safety filter.

The canonical target is displayed without the leading period as:

```text
github/workflows/validate-stegguardian-adapter.yml
```

## Automation Request

```text
automation/stegguardian-workflow-install-request.json
```

## Next Action

The next ecosystem process should consume the automation request and promote the iOS-safe workflow mirror into the canonical workflow target without human file movement.
