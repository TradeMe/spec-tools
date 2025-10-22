"""Command-line interface for spec-tools."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .linter import SpecLinter
from .markdown_link_validator import MarkdownLinkValidator
from .markdown_schema_validator import MarkdownSchemaValidator


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


def cmd_check_links(args) -> int:
    """Execute the check-links command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        validator = MarkdownLinkValidator(
            root_dir=Path(args.directory),
            config_file=args.config,
            timeout=args.timeout,
            max_concurrent=args.max_concurrent,
            check_external=not args.no_external,
            use_gitignore=not args.no_gitignore,
        )

        # Run validation
        result = validator.validate(verbose=args.verbose)

        # Print results
        if args.verbose or not result.is_valid:
            print(result)
        elif result.is_valid:
            print(
                f"✓ All {result.valid_links} links valid "
                f"({result.private_links} private links skipped)"
            )

        # Return appropriate exit code
        return 0 if result.is_valid else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def cmd_check_schema(args) -> int:
    """Execute the check-schema command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        validator = MarkdownSchemaValidator(
            root_dir=Path(args.directory),
            config_file=args.config,
            respect_gitignore=not args.no_gitignore,
        )

        # Run validation
        result = validator.validate()

        # Print results
        if args.verbose or not result.is_valid:
            print(result)
        elif result.is_valid:
            print(f"✓ All {result.valid_files} markdown files conform to schema")

        # Return appropriate exit code
        return 0 if result.is_valid else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
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

    # Check-links command
    check_links_parser = subparsers.add_parser(
        "check-links",
        help="Validate hyperlinks in markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check links in current directory
  spec-tools check-links

  # Check links in a specific directory
  spec-tools check-links /path/to/docs

  # Use a custom config file
  spec-tools check-links --config .myconfigfile

  # Skip external URL validation
  spec-tools check-links --no-external

  # Set timeout for external URLs
  spec-tools check-links --timeout 30

Configuration file format (.speclinkconfig):
  The config file lists private URL patterns to skip validation.
  Each line is a pattern. Lines starting with # are comments.

  Example .speclinkconfig:
    # Private domains
    internal.company.com
    localhost

    # Private URL prefixes
    https://private.example.com/
    http://localhost:
    http://127.0.0.1:

Link validation rules:
  - Internal links: Checked relative to the markdown file
  - Anchors: Validated against headings in target files
  - External URLs: HTTP requests verify accessibility
  - Private URLs: Matched patterns are skipped
        """,
    )

    check_links_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to check (default: current directory)",
    )

    check_links_parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="Path to config file (default: .speclinkconfig)",
    )

    check_links_parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        default=10,
        help="Timeout for external URL requests in seconds (default: 10)",
    )

    check_links_parser.add_argument(
        "--max-concurrent",
        "-m",
        type=int,
        default=10,
        help="Maximum concurrent external URL requests (default: 10)",
    )

    check_links_parser.add_argument(
        "--no-external",
        action="store_true",
        help="Skip external URL validation",
    )

    check_links_parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore patterns",
    )

    check_links_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    check_links_parser.set_defaults(func=cmd_check_links)

    # Check-schema command
    check_schema_parser = subparsers.add_parser(
        "check-schema",
        help="Validate markdown files against a defined schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check schema in current directory
  spec-tools check-schema

  # Check schema in a specific directory
  spec-tools check-schema /path/to/specs

  # Use a custom config file
  spec-tools check-schema --config .myschemaconfig

Schema validation includes:
  - Required and optional metadata fields
  - Heading structure and hierarchy
  - EARS format compliance for requirements
  - Body content validation

Default schema (no config file):
  - Files: specs/*.md
  - Metadata: ID, Version, Date, Status
  - Headings: H1 (Specification: ...), H2 (Overview), H2 (Requirements)
  - EARS format validation for requirements sections
        """,
    )

    check_schema_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to check (default: current directory)",
    )

    check_schema_parser.add_argument(
        "--config",
        "-c",
        default=None,
        help="Path to schema config file (default: .specschemaconfig)",
    )

    check_schema_parser.add_argument(
        "--no-gitignore",
        action="store_true",
        help="Don't respect .gitignore patterns",
    )

    check_schema_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    check_schema_parser.set_defaults(func=cmd_check_schema)

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
