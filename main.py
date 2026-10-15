"""Command-line entry point for the kidney classifier."""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

COMMANDS = {
    "train-baseline": (
        PROJECT_ROOT / "src" / "cnnClassifier" / "pipeline"
        / "stage_03_model_training.py"
    ),
    "evaluate-validation": (
        PROJECT_ROOT / "src" / "cnnClassifier" / "pipeline"
        / "stage_04_model_evaluation.py"
    ),
    "fine-tune": (
        PROJECT_ROOT / "src" / "cnnClassifier" / "pipeline"
        / "stage_05_fine_tuning.py"
    ),
}


def main():
    parser = argparse.ArgumentParser(
        description="Four-class kidney image classification project."
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=(
            "train-baseline",
            "fine-tune",
            "evaluate-validation",
            "web",
        ),
        help=(
            "train-baseline: train the baseline model; "
            "fine-tune: fine-tune the model; "
            "evaluate-validation: evaluate on val only; "
            "web: start the local interface"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Archive existing outputs before fine-tuning again.",
    )
    args = parser.parse_args()

    if args.force and args.command != "fine-tune":
        parser.error("--force is only valid with fine-tune.")

    if args.command is None:
        parser.print_help()
        print("\nNo training or evaluation was started.")
        return 0

    if args.command == "web":
        target = PROJECT_ROOT / "app.py"
        command = [sys.executable, str(target)]
    else:
        target = COMMANDS[args.command]
        command = [sys.executable, str(target)]
        if args.command == "fine-tune" and args.force:
            command.append("--force")

    if not target.is_file():
        parser.error("Required script not found: {}".format(target))

    result = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
