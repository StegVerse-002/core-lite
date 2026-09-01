# Transition Ledger Mirror Handoff

Repository: `StegVerse-002/core-lite`

Every durable transition owned here is recorded first in this repository ledger. Repository replay/reconstruction terminates at this level without requiring organization or ecosystem replay.

- Contract: `.stegverse/transition-ledger/contract.json`
- Emitter: `.stegverse/transition-ledger/emit.py`
- Default durable root: `$XDG_STATE_HOME/stegverse/repo-ledgers/StegVerse-002/core-lite`

Receipts are append-only and hash-linked. Only evidence needed for organization reconstruction propagates to `StegVerse-002/.github`. Recording creates no execution, standing, admission, credential, publication, or lifecycle authority.
