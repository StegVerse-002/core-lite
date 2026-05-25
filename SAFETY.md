# SAFETY.md — StegVerse-002/core-lite

## Do not store in this repo

- Passwords or passphrases
- Seed phrases or private keys
- Raw API keys or tokens
- Bank credentials or financial secrets
- Full SSNs or unredacted government identifiers
- Unprotected legal secrets
- Private cryptographic material

## Threat model

### Plain-text risk
All files in this repo are readable by anyone with repo access.
Do not commit sensitive material without encryption.

### Device risk
If your device is lost or compromised, repo access tokens must be rotated immediately.

### Cloud sync risk
If this repo syncs to a cloud service, all content is subject to that service's policies.

### AI-upload risk
Do not upload the full vault or full repo contents to an external AI system.
Use context packets with explicit allowed_use declarations.

### Sharing risk
Context packets shared outside StegVerse-002 must declare target_entity, allowed_use,
forbidden_use, and STOP condition before leaving the vault.

## Default policies

```
default_privacy_class: private
default_ai_use: review_required
default_external_sharing: denied
default_training_use: denied
default_publication_use: denied
default_identity_authority: false
```

## On encryption

TV/TVC layers provide signing and verification.
They do not provide at-rest encryption of repo content.
For sensitive data, use separate encrypted storage and reference by hash only.
