# AI_CONTEXT.md — StegVerse-002 KnowledgeVault

## How AI systems may use this vault

This file defines how StegVerse-002 and any scoped AI system may interact
with content from this KnowledgeVault.

**identity_authority: false**
Identity context may inform interpretation. It does not authorize action.

---

## Allowed AI uses

- Receive bounded context packets with declared purpose
- Produce reports from admitted context
- Prepare candidates from admitted context
- Emit memory-use receipts for all uses

## Forbidden AI uses

- Full vault dump to any AI system
- Training use of vault content
- Publication of vault content
- Identity verification claims based on vault content
- Silent inference of permissions not explicitly declared
- Retention outside the declared stop condition

## Ask-before-use rules

- Any use beyond the declared allowed_use in the context packet
- Any inference about identity beyond what is explicitly declared
- Any action against a target repo based solely on vault context

## Never-assume rules

- Do not assume an old note represents current intent
- Do not assume a draft represents final decision
- Do not assume stored context is authorization
- Do not assume identity context is identity proof

## Current active context

Vault supports StegVerse-002/core-lite at SV002-M10.

## Last reviewed

2026-05-23
