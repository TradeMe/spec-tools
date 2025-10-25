"""Command-line interface for spec-tools."""

import argparse
import sys
from pathlib import Path

from .config import load_config, merge_config_with_args
from .dsl.type_definitions import TypeDefinitionLoader
from .dsl.validator import DSLValidator
from .linter import SpecLinter
from .markdown_link_validator import MarkdownLinkValidator
from .markdown_schema_validator import MarkdownSchemaValidator
from .spec_coverage_linter import SpecCoverageLinter
from .structure_linter import StructureLinter
from .unique_specs_linter import UniqueSpecsLinter


def cmd_lint(args) -> int:
    """Execute the lint command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Load config from pyproject.toml and merge with CLI args
        config = load_config(Path(args.directory))
        merged_config = merge_config_with_args(config, args, "lint")

        linter = SpecLinter(
            root_dir=Path(args.directory),
            allowlist_file=merged_config["allowlist_file"],
            use_gitignore=merged_config["use_gitignore"],
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
        # Load config from pyproject.toml and merge with CLI args
        config = load_config(Path(args.directory))
        merged_config = merge_config_with_args(config, args, "check-links")

        validator = MarkdownLinkValidator(
            root_dir=Path(args.directory),
            config_file=merged_config["config_file"],
            timeout=merged_config["timeout"],
            max_concurrent=merged_config["max_concurrent"],
            check_external=merged_config["check_external"],
            use_gitignore=merged_config["use_gitignore"],
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


def cmd_check_coverage(args) -> int:
    """Execute the check-coverage command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Load config from pyproject.toml and merge with CLI args
        config = load_config(Path(args.directory))
        merged_config = merge_config_with_args(config, args, "check-coverage")

        linter = SpecCoverageLinter(
            root_dir=Path(args.directory),
            specs_dir=Path(args.specs_dir) if args.specs_dir else None,
            tests_dir=Path(args.tests_dir) if args.tests_dir else None,
            min_coverage=merged_config["min_coverage"],
        )

        # Run linter
        result = linter.lint()

        # Print results
        print(result)

        # Return appropriate exit code
        return 0 if result.is_valid else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def cmd_check_structure(args) -> int:
    """Execute the check-structure command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        linter = StructureLinter(
            root_dir=Path(args.directory),
            specs_dir=Path(args.specs_dir) if args.specs_dir else None,
            tests_dir=Path(args.tests_dir) if args.tests_dir else None,
        )

        # Run linter
        result = linter.lint()

        # Print results
        print(result)

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
        # Load config from pyproject.toml and merge with CLI args
        config = load_config(Path(args.directory))
        merged_config = merge_config_with_args(config, args, "check-schema")

        validator = MarkdownSchemaValidator(
            root_dir=Path(args.directory),
            config_file=merged_config["config_file"],
            respect_gitignore=merged_config["respect_gitignore"],
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


def cmd_check_unique_specs(args) -> int:
    """Execute the check-unique-specs command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        linter = UniqueSpecsLinter(
            root_dir=Path(args.directory),
            specs_dir=Path(args.specs_dir) if args.specs_dir else None,
        )

        # Run linter
        result = linter.lint()

        # Print results
        print(result)

        # Return appropriate exit code
        return 0 if result.is_valid else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def cmd_validate_dsl(args) -> int:
    """Execute the validate-dsl command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Type definitions directory
        type_dir = Path(args.type_dir)
        if not type_dir.exists():
            print(f"Error: Type definitions directory not found: {type_dir}", file=sys.stderr)
            return 1

        # Load type definitions
        loader = TypeDefinitionLoader(type_dir)
        loader.load_all()

        if args.verbose:
            print(f"Loaded {len(loader.modules)} module type(s)")
            print(f"Loaded {len(loader.classes)} shared class type(s)")
            print(f"Loaded {len(loader.content_validators)} content validator(s)")
            print()

        # Create validator
        validator = DSLValidator(loader)

        # Run validation
        root_path = Path(args.directory)
        result = validator.validate(root_path)

        # Print results
        print(result)

        # Return appropriate exit code
        return 0 if result.success else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            raise
        return 1


def main(argv: list | None = None) -> int:
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
        default=None,
        help="Timeout for external URL requests in seconds (default: 10)",
    )

    check_links_parser.add_argument(
        "--max-concurrent",
        "-m",
        type=int,
        default=None,
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

    # Check-coverage command
    check_coverage_parser = subparsers.add_parser(
        "check-coverage",
        help="Validate that all spec requirements have corresponding tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check spec coverage in current directory
  spec-tools check-coverage

  # Check coverage in a specific directory
  spec-tools check-coverage /path/to/project

  # Use custom specs and tests directories
  spec-tools check-coverage --specs-dir my-specs --tests-dir my-tests

How it works:
  This tool validates spec-to-test traceability by:
  1. Extracting requirement IDs from spec files (e.g., REQ-001, NFR-001)
  2. Finding pytest.mark.req markers in test files
  3. Verifying each requirement has at least one test
  4. Reporting requirements without tests

Test marking format:
  Use pytest markers to link tests to requirements:

  @pytest.mark.req("REQ-001")
  def test_something():
      '''Test for requirement REQ-001.'''
      ...

  # For tests covering multiple requirements:
  @pytest.mark.req("REQ-001", "REQ-002")
  def test_combined():
      '''Test for requirements REQ-001 and REQ-002.'''
      ...
        """,
    )

    check_coverage_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory of the project (default: current directory)",
    )

    check_coverage_parser.add_argument(
        "--specs-dir",
        default=None,
        help="Directory containing spec files (default: <directory>/specs)",
    )

    check_coverage_parser.add_argument(
        "--tests-dir",
        default=None,
        help="Directory containing test files (default: <directory>/tests)",
    )

    check_coverage_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    check_coverage_parser.add_argument(
        "--min-coverage",
        type=float,
        default=None,
        help="Minimum acceptable coverage percentage (default: 100.0 or from pyproject.toml)",
    )

    check_coverage_parser.set_defaults(func=cmd_check_coverage)

    # Check-structure command
    check_structure_parser = subparsers.add_parser(
        "check-structure",
        help="Validate that spec files have corresponding test files/directories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check structure in current directory
  spec-tools check-structure

  # Check structure in a specific directory
  spec-tools check-structure /path/to/project

  # Use custom specs and tests directories
  spec-tools check-structure --specs-dir my-specs --tests-dir my-tests

How it works:
  This tool validates spec-to-test structure alignment by:
  1. Finding all spec files in the specs directory
  2. Verifying each spec has a corresponding test file or directory
  3. Reporting specs without tests

Structure conventions:
  For a spec file: specs/foo-bar.md
  Expected test paths:
    - tests/test_foo_bar.py  (single test file)
    - tests/foo_bar/         (test directory)

  Note: Having test files without corresponding specs is allowed.
  These are typically unit tests that don't directly correspond to
  a spec requirement (e.g., testing implementation details).
        """,
    )

    check_structure_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory of the project (default: current directory)",
    )

    check_structure_parser.add_argument(
        "--specs-dir",
        default=None,
        help="Directory containing spec files (default: <directory>/specs)",
    )

    check_structure_parser.add_argument(
        "--tests-dir",
        default=None,
        help="Directory containing test files (default: <directory>/tests)",
    )

    check_structure_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    check_structure_parser.set_defaults(func=cmd_check_structure)

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

    # Check-unique-specs command
    check_unique_specs_parser = subparsers.add_parser(
        "check-unique-specs",
        help="Validate that all spec IDs and requirement IDs are unique",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check unique specs in current directory
  spec-tools check-unique-specs

  # Check unique specs in a specific directory
  spec-tools check-unique-specs /path/to/project

  # Use custom specs directory
  spec-tools check-unique-specs --specs-dir my-specs

How it works:
  This tool validates spec and requirement ID uniqueness by:
  1. Extracting SPEC IDs from all spec files (e.g., SPEC-001, SPEC-002)
  2. Verifying each SPEC ID appears in only one file
  3. Extracting requirement IDs from each spec (e.g., REQ-001, NFR-001)
  4. Verifying each requirement ID appears only once within its spec
  5. Ensuring globally unique requirement IDs (SPEC-001/REQ-001)

Validation rules:
  - Each spec file must have a unique SPEC ID
  - Within each spec, requirement IDs must be unique (no duplicate REQ-001)
  - The combination of SPEC ID and requirement ID must be globally unique
        """,
    )

    check_unique_specs_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Root directory of the project (default: current directory)",
    )

    check_unique_specs_parser.add_argument(
        "--specs-dir",
        default=None,
        help="Directory containing spec files (default: <directory>/specs)",
    )

    check_unique_specs_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    check_unique_specs_parser.set_defaults(func=cmd_check_unique_specs)

    # Validate-DSL command
    validate_dsl_parser = subparsers.add_parser(
        "validate-dsl",
        help="Validate markdown documents against DSL type definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate documents using type definitions in .spec-types
  spec-tools validate-dsl

  # Validate specific directory
  spec-tools validate-dsl specs/

  # Use custom type definitions directory
  spec-tools validate-dsl --type-dir my-types/

How it works:
  The DSL validator implements a multi-pass validation architecture:
  1. Parse markdown documents into AST
  2. Build hierarchical section trees
  3. Assign types based on file patterns
  4. Validate document structure
  5. Validate section content
  6. Extract references (links)
  7. Resolve and validate references

Type definitions:
  Type definitions are YAML files that describe:
  - Module types (e.g., Requirement, Contract, ADR)
  - Class types (reusable section patterns)
  - Content validators (e.g., EARS, Gherkin)
  - Reference constraints (cardinality, type checking)

  Directory structure:
    .spec-types/
      config.yaml              # Global configuration
      modules/
        requirement.yaml       # Module type definitions
        contract.yaml
      classes/
        test-case.yaml         # Shared class definitions
      content-validators/
        gherkin.yaml           # Content validators

Reference validation:
  Links are treated as typed references:
  - [text](MODULE-ID) -> Module instance reference
  - [text](#CLASS-ID) -> Class instance reference
  - [text](http://...) -> External reference (not validated)

  References are validated for:
  - Target existence
  - Type matching
  - Cardinality constraints
        """,
    )

    validate_dsl_parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to validate (default: current directory)",
    )

    validate_dsl_parser.add_argument(
        "--type-dir",
        "-t",
        default=".spec-types",
        help="Path to type definitions directory (default: .spec-types)",
    )

    validate_dsl_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    validate_dsl_parser.set_defaults(func=cmd_validate_dsl)

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
