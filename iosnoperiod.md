# iosnoperiod Mirror

This bundle includes an `iosnoperiod/` mirror for paths that contain leading-dot directories.

The canonical workflow path is:

```text
.github/workflows/core-lite-intake.yml
```

The iOS-safe mirror path is:

```text
iosnoperiod/github/workflows/core-lite-intake-yml
```

In this mirror, `iosnoperiod/` equals repo root for placement purposes, and all leading dots and filename periods are removed from the mirror path to prevent iOS from hiding, stripping, or misplacing dot-prefixed files/directories.

Use the canonical path when uploading to GitHub.

Use the mirror only as a fallback reference if iOS mishandles the canonical dot path.
