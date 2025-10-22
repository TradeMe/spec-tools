"""Command-line interface for spec-tools."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .linter import SpecLinter


def cmd_lint(args) -> int:
    """Execute the lint command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        linter = SpecLinter(
            root_dir=Path(args.directory),
            allowlist_file=args.allowlist,
            use_gitignore=not args.no_gitignore,
        )

        # Run lint
        result = linter.lint()

        # Print results
        if args.verbose or not result.is_valid:
            print(result)
        elif result.is_valid:
            print(f"✓ All {result.total_files} files matched allowlist patterns")

        # Return appropriate exit code
        return 0 if result.is_valid else 1

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def main(argv: Optional[list] = None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        prog="spec-tools",
        description="Tools for spec-driven development",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    # Create subparsers for different tools
    subparsers = parser.add_subparsers(dest="command", help="Available tools")

    # Lint command
    lint_parser = subparsers.add_parser(
        "lint",
        help="Validate that all files match patterns in an allowlist",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lint the current directory
  spec-tools lint

  # Lint a specific directory
  spec-tools lint /path/to/project

  # Use a custom allowlist file
  spec-tools lint --allowlist .myallowlist

  # Don't use .gitignore patterns
  spec-tools lint --no-gitignore

Allowlist file format:
  The allowlist file uses gitignore-style glob patterns.
  Each line is a pattern. Lines starting with # are comments.

  Example .specallowlist:
    # Documentation
    *.md
    docs/**/*.rst

    # Source code
    src/**/*.py
    tests/**/*.py

    # Config files
    *.toml
    *.yaml

    # Specs with specific naming
    specs/research-[0-9][0-9][0-9]-*.md
        """,
    )

    lint_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to lint (default: current directory)",
    )

    lint_parser.add_argument(
        "--allowlist",
        "-a",
        default=None,
        help="Path to allowlist file (default: .specallowlist)",
    )

    lint_parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore patterns",
    )

    lint_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    lint_parser.set_defaults(func=cmd_lint)

    # Parse arguments
    args = parser.parse_args(argv)

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 1

    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
