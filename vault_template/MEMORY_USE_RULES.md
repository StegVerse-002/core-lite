# MEMORY_USE_RULES.md — StegVerse-002 KnowledgeVault

## Default memory-use policy

```
default_privacy_class: private
default_ai_use: review_required
default_external_sharing: denied
default_training_use: denied
default_publication_use: denied
default_mutation_authority: false
```

## Allowed uses by stage

| Stage | Allowed use |
|-------|-------------|
| SV002-M0 to M2 | context, report |
| SV002-M3 to M4 | context, report, candidate_preparation |
| SV002-M5+ | context, report, candidate_preparation, instruction_packet |

## Forbidden uses (all stages)

- Training data
- Publication without explicit consent
- Identity verification claims
- Production mutation without quorum
- Silent memory retention beyond STOP condition

## Review-required uses

- Any use of sensitive or restricted content
- Any identity-adjacent inference
- Any use beyond declared allowed_use in context packet

## Receipt requirements

Every admitted memory use must produce a memory-use receipt containing:
- vault_id
- packet_id
- actor
- purpose
- decision
- files_used
- allowed_use
- forbidden_use
- stop_condition
- receipt_hash
- previous_receipt_hash

## STOP condition rules

Every context packet must declare a STOP condition.
Memory use stops when the STOP condition is met.
