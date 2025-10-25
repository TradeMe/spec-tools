#!/usr/bin/env python3
"""
Parse GitHub Actions workflow file and extract commands to run locally.

This script reads the CI workflow YAML and extracts all the run commands
from the lint and test jobs, allowing them to be executed in pre-commit hooks.
"""

import argparse
import sys
from pathlib import Path

import yaml


def parse_workflow(workflow_path: Path) -> dict[str, list[str]]:
    """
    Parse GitHub Actions workflow and extract run commands.

    Args:
        workflow_path: Path to the workflow YAML file

    Returns:
        Dictionary with 'lint' and 'test' keys containing lists of commands
    """
    with open(workflow_path) as f:
        workflow = yaml.safe_load(f)

    commands = {"lint": [], "test": []}

    jobs = workflow.get("jobs", {})

    # Extract lint commands
    lint_job = jobs.get("lint", {})
    for step in lint_job.get("steps", []):
        if "run" in step:
            # Skip setup steps
            if any(
                x in step.get("name", "").lower()
                for x in ["install uv", "set up python", "install dependencies"]
            ):
                continue
            commands["lint"].append(step["run"])

    # Extract test commands
    test_job = jobs.get("test", {})
    for step in test_job.get("steps", []):
        if "run" in step:
            # Skip setup steps and coverage upload
            if any(
                x in step.get("name", "").lower()
                for x in [
                    "install uv",
                    "set up python",
                    "install dependencies",
                    "upload coverage",
                ]
            ):
                continue
            commands["test"].append(step["run"])

    return commands


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse GitHub Actions workflow and extract commands"
    )
    parser.add_argument(
        "--workflow",
        type=Path,
        default=Path(".github/workflows/ci.yml"),
        help="Path to workflow file (default: .github/workflows/ci.yml)",
    )
    parser.add_argument(
        "--job",
        choices=["lint", "test", "all"],
        default="all",
        help="Which job commands to extract (default: all)",
    )
    parser.add_argument(
        "--format",
        choices=["bash", "json"],
        default="bash",
        help="Output format (default: bash)",
    )

    args = parser.parse_args()

    if not args.workflow.exists():
        print(f"Error: Workflow file not found: {args.workflow}", file=sys.stderr)
        return 1

    try:
        commands = parse_workflow(args.workflow)
    except Exception as e:
        print(f"Error parsing workflow: {e}", file=sys.stderr)
        return 1

    # Output commands
    if args.format == "bash":
        jobs_to_print = []
        if args.job in ("lint", "all"):
            jobs_to_print.append(("lint", commands["lint"]))
        if args.job in ("test", "all"):
            jobs_to_print.append(("test", commands["test"]))

        for _job_name, job_commands in jobs_to_print:
            for cmd in job_commands:
                print(cmd)
    elif args.format == "json":
        import json

        if args.job == "all":
            print(json.dumps(commands, indent=2))
        else:
            print(json.dumps(commands[args.job], indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
