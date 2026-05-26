# PRIVACY_CLASSES.md — StegVerse-002 KnowledgeVault

## Classes

### public
Content that may be shared freely.
Allowed AI use: context, report, candidate_preparation, publication.
Review requirement: none.

### shareable
Content that may be shared with explicit consent.
Allowed AI use: context, report, candidate_preparation.
Review requirement: confirm recipient.

### private
Default class. Content for personal or project use only.
Allowed AI use: context, report (within bounded context packet only).
Review requirement: explicit context packet required.

### sensitive
Content requiring extra care: personal data, health, legal, financial.
Allowed AI use: context only (within bounded context packet with explicit allowed_use).
Review requirement: mandatory before any AI use.

### restricted
Highest protection. Minimal distribution.
Allowed AI use: denied by default.
Review requirement: manual operator approval required.

### unknown
Privacy class not determined.
Allowed AI use: denied by default.
Review requirement: classification required before any use.

## Default

All new content defaults to: **private**
