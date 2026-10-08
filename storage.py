import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from workflow import (
    assess_readiness,
    build_clarification_questions,
    validate_launch_pack,
)

RUNS_DIR = Path(__file__).resolve().parent / "runs"


def save_launch_record(brief: str, facts: dict, pack: str) -> Path:
    decision = assess_readiness(facts)
    if decision["status"] != "Ready to launch":
        missing = ", ".join(decision["missing_information"])
        raise ValueError(f"Intake cannot launch; missing: {missing}")

    problems = validate_launch_pack(pack)
    if problems:
        raise ValueError("Invalid launch pack: " + "; ".join(problems))

    created_at = datetime.now(timezone.utc)
    run_id = created_at.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True)

    (run_dir / "launch-pack.md").write_text(pack, encoding="utf-8")

    record = {
        "run_id": run_id,
        "created_at_utc": created_at.isoformat(),
        "status": "Launched",
        "decision_reason": (
            "Required intake fields were present and the launch pack passed validation."
        ),
        "original_brief": brief,
        "extracted_facts": facts,
        "launch_pack_file": "launch-pack.md",
    }
    (run_dir / "decision.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return run_dir

def save_needs_information_record(brief: str, facts: dict) -> Path:
    decision = assess_readiness(facts)
    if decision["status"] != "Needs information":
        raise ValueError("This intake has enough information to launch")

    created_at = datetime.now(timezone.utc)
    run_id = created_at.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True)

    missing = decision["missing_information"]
    record = {
        "run_id": run_id,
        "created_at_utc": created_at.isoformat(),
        "status": "Needs information",
        "decision_reason": "Required intake fields are missing; search was not launched.",
        "original_brief": brief,
        "extracted_facts": facts,
        "missing_information": missing,
        "clarification_questions": build_clarification_questions(missing),
    }
    (run_dir / "decision.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return run_dir