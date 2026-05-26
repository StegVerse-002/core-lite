# KnowledgeVault → StegVerse-002 Context Packet Flow

## Flow

```
KnowledgeVault
  ↓ user selects files
Context Packet Manifest (vault_template/context_packets/)
  ↓
core_lite.knowledgevault.intake
  ↓
CGE admissibility check
  ↓
StegVerse-002 receives bounded context
  ↓
memory-use receipt emitted
  ↓
STOP enforced
```

## Rules

- StegVerse-002 never receives the full vault
- Context is not consent
- Memory is not authority
- Every use is receipted
- STOP condition is declared in every packet

## Creating a context packet

1. Copy `templates/context_packet_template.json`
2. Fill in packet_id, vault_id, target_stage, purpose
3. Declare allowed_use and forbidden_use explicitly
4. Declare a STOP condition
5. List included_files (select only what is needed)
6. Save to `vault_template/context_packets/`
7. Run via dispatcher: `task_id: kv.context.packet.intake`
