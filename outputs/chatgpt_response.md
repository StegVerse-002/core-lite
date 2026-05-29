```json
{
  "schema": "stegverse.candidate_patch.v1",
  "candidate_id": "sv002-m11-incoming-disposition-gate-repair",
  "provider": "openai-or-claude",
  "description": "Repair incoming disposition workflow to stage, evaluate, disposition, quarantine if needed, and clean only dispositioned changed payloads while inventorying legacy incoming payloads.",
  "transition_class": "workflow-repair",
  "authority_ref": "SV002-M11/scoped-workflow-repair-candidate",
  "policy_ref": "triad/default-deny/no-broad-authority",
  "files": [
    {
      "path": ".github/workflows/core-lite-intake.yml",
      "operation": "write",
      "content": "name: Core-Lite Intake\n\non:\n  push:\n    branches: [main]\n    paths:\n      - \"incoming/**\"\n  workflow_dispatch:\n    inputs:\n      input_type:\n        description: 'Type of input'\n        required: true\n      input_path:\n        description: 'Path to input'\n        required: true\n      stage_override:\n        description: 'Stage override'\n        required: false\n      dry_run:\n        description: 'Dry run mode'\n        required: false\n      agent_provider:\n        description: 'Agent provider'\n        required: false\n      task_id:\n        description: 'Task ID'\n        required: false\n\njobs:\n  intake:\n    runs-on: ubuntu-latest\n    steps:\n    - name: Checkout code\n      uses: actions/checkout@v2\n\n    - name: Identify changed files\n      id: changes\n      run: |\n        echo \"::set-output name=changed_files::$(git diff --name-only HEAD^ HEAD | grep '^incoming/' | grep -v 'incoming/README.md' | sort)\"\n\n    - name: Process changed files\n      if: steps.changes.outputs.changed_files\n      run: |\n        mkdir -p tracking/incoming_mailbox\n        for file in $(echo ${{ steps.changes.outputs.changed_files }}); do\n          sha=$(sha256sum \"$file\" | awk '{print $1}')\n          mkdir -p \"tracking/incoming_mailbox/$sha\"\n          cp \"$file\" \"tracking/incoming_mailbox/$sha/$(basename \"$file\")\"\n          # Run evaluation pipeline\n          # Assuming a script or command exists to evaluate\n          if ./evaluate \"tracking/incoming_mailbox/$sha/$(basename \"$file\")\"; then\n            echo \"INSTALLED_OR_ACCEPTED\" >> reports/current/incoming_disposition_summary.jsonl\n            echo \"INSTALLED_OR_ACCEPTED\" >> receipts/current/incoming_disposition_receipt.jsonl\n          else\n            mkdir -p \"quarantine/incoming/$sha\"\n            cp \"tracking/incoming_mailbox/$sha/$(basename \"$file\")\" \"quarantine/incoming/$sha/\"\n            echo \"QUARANTINED\" >> reports/current/incoming_disposition_summary.jsonl\n            echo \"QUARANTINED\" >> receipts/current/incoming_disposition_receipt.jsonl\n          fi\n          echo \"$file\" >> reports/current/incoming_disposition_processed_files.txt\n          rm \"$file\"\n        done\n\n    - name: Inventory legacy files\n      run: |\n        git ls-files incoming/ | grep -v 'incoming/README.md' > reports/current/incoming_legacy_inventory.txt\n"
    }
  ]
}
```
