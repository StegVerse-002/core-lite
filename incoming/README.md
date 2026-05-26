# incoming/

Place candidate ingestion bundles here.

Supported forms:

```text
incoming/<bundle>.zip
incoming/<expanded_bundle>/
```

Do not place ordinary repo files here unless they are inside a bundle structure with a valid manifest.

The ingestion engine validates manifest, hashes, path policy, and writes reports/receipts.
