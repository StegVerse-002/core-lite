"""
core_lite.cli — StegVerse-002 command-line entry point.

Usage:
    python -m core_lite.cli run [OPTIONS]
    python -m core_lite.cli task --task-id TASK_ID [OPTIONS]
    python -m core_lite.cli status
    python -m core_lite.cli repair --target-repo REPO [OPTIONS]
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("core_lite.cli")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_run(args):
    from core_lite.intake import IntakeOrchestrator

    log.info("=== StegVerse-002 core-lite intake run ===")
    log.info("entity=%s  stage=%s  skip_tasks=%s  task_id=%s",
             args.entity, args.stage, args.skip_tasks, args.task_id or "")

    orchestrator = IntakeOrchestrator(
        repo_root=Path(args.repo_root),
        entity=args.entity,
        stage=args.stage,
        skip_tasks=args.skip_tasks,
        task_id=args.task_id or "",
        dry_run=args.dry_run,
    )
    result = orchestrator.run()

    # Write run summary
    summary_path = Path(args.repo_root) / "reports" / "current" / "core_lite_run_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(result, f, indent=2)

    log.info("Run summary written to %s", summary_path)

    if result.get("status") == "success":
        log.info("STOP condition: intake succeeded with task_id=%s skip_tasks=%s",
                 args.task_id or "blank", args.skip_tasks)
        sys.exit(0)
    else:
        log.error("Intake did not succeed: %s", result.get("error", "unknown"))
        sys.exit(1)


def cmd_task(args):
    from tools.scripts.task_dispatcher import TaskDispatcher

    log.info("=== Declared task: %s ===", args.task_id)
    dispatcher = TaskDispatcher(
        task_id=args.task_id,
        catalog_path=Path(args.catalog),
        entity=args.entity,
        stage=args.stage,
        dry_run=args.dry_run,
    )
    result = dispatcher.run()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


def cmd_status(args):
    status_path = Path("STATUS.md")
    stage_map_path = Path("tracking/stegverse-002/stage_map.json")

    print("=== StegVerse-002/core-lite STATUS ===")
    if status_path.exists():
        print(status_path.read_text())

    if stage_map_path.exists():
        with open(stage_map_path) as f:
            stage_map = json.load(f)
        print("\n=== Stage Map ===")
        print(json.dumps(stage_map, indent=2))


def cmd_repair(args):
    from tools.repair.sv001_repair import SV001Repair

    log.info("=== StegVerse-001 repair — target: %s ===", args.target_repo)
    repair = SV001Repair(
        target_repo=args.target_repo,
        entity=args.entity,
        dry_run=args.dry_run,
    )
    result = repair.run()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


def main():
    parser = argparse.ArgumentParser(
        prog="core_lite",
        description="StegVerse-002 core-lite CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="Run core-lite intake")
    p_run.add_argument("--repo-root", default=".", help="Repo root path")
    p_run.add_argument("--entity", default="StegVerse-002")
    p_run.add_argument("--stage", default="SV002-M5")
    p_run.add_argument("--task-id", default="", help="Declared task ID (blank = default intake)")
    p_run.add_argument("--skip-tasks", action="store_true", default=True)
    p_run.add_argument("--no-skip-tasks", dest="skip_tasks", action="store_false")
    p_run.add_argument("--dry-run", action="store_true", default=False)

    # task
    p_task = sub.add_parser("task", help="Run a declared task by ID")
    p_task.add_argument("--task-id", required=True)
    p_task.add_argument("--catalog", default="tools/tasks/task_catalog.json")
    p_task.add_argument("--entity", default="StegVerse-002")
    p_task.add_argument("--stage", default="SV002-M5")
    p_task.add_argument("--dry-run", action="store_true", default=False)

    # status
    sub.add_parser("status", help="Show current status and stage map")

    # repair
    p_repair = sub.add_parser("repair", help="Repair StegVerse-001 instance")
    p_repair.add_argument("--target-repo", required=True)
    p_repair.add_argument("--entity", default="StegVerse-002")
    p_repair.add_argument("--dry-run", action="store_true", default=False)

    args = parser.parse_args()

    dispatch = {
        "run": cmd_run,
        "task": cmd_task,
        "status": cmd_status,
        "repair": cmd_repair,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
