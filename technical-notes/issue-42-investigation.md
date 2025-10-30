# Issue #42 Investigation: validate-dsl Reference Resolution Failures

**Issue**: validate-dsl fails to resolve references between validated documents
**Date**: 2025-10-30
**Status**: Root cause identified, solution proposed

## Problem Statement

The `validate-dsl` command cannot resolve cross-directory file path references, even when both source and target documents are being validated. This causes validation failures in real-world documentation repositories.

### Reported Symptoms

- File path references like `./milestones/milestone-0-hello-world` fail to resolve
- Cross-directory references like `../../../roadmap/milestones/milestone-0-hello-world` fail
- ~548 reference resolution failures in a typical project (out of 892 total failures)
- Additional failures from unwanted directories: `.claude/` (341), `.venv/` (3)

## Root Cause Analysis

### Initial Hypothesis (INCORRECT)

The issue description suggested that `_resolve_by_file_path()` in `reference_resolver.py` was broken and couldn't handle relative paths across directories.

### Actual Root Cause (CONFIRMED)

The `_resolve_by_file_path()` function works correctly. The real problem is:

**Files can only be resolved if they're registered in the ID registry, and files are only registered if they match a type definition.**

#### The Registration Flow

```
1. validator.validate(root_path)
2. Find all *.md files with root_path.rglob("*.md")
3. For each file:
   - Try to match against type definitions
   - If match: Register in ID registry
   - If no match: Skip (not registered)
4. Extract and resolve references
5. References to unregistered files fail
```

#### Code Evidence

In `spec_check/dsl/validator.py:304-319`:

```python
def _assign_type_and_register(self, doc_ctx: DocumentContext) -> None:
    """Pass 3: Assign module type and register IDs."""
    # Find matching module definition
    module_def = self.type_registry.get_module_for_file(doc_ctx.file_path)

    if not module_def:
        # No matching type definition - this might be ok
        self.info.append(...)
        return  # ← File is NOT registered!

    # ... only registered if type matches
```

### Reproduction

#### Test Case 1: Files Without Type Definitions (FAILS)

```
roadmap/milestones/milestone-0-hello-world.md  # No builtin type matches
roadmap/roadmap.md                              # References ./milestones/...

Result: "Module reference './milestones/milestone-0-hello-world' not found"
```

The milestone file is never registered in the ID registry because it doesn't match any of the builtin types (Job, Requirement, ADR, Specification, Principles).

#### Test Case 2: Files With Type Definitions (SUCCEEDS)

```
specs/architecture/ADR-011.md  # Matches ADR pattern
specs/architecture/ADR-012.md  # References ./ADR-011.md

Result: Validation succeeds ✓
```

The ADR files match the builtin ADR type pattern, get registered, and references resolve correctly.

### The Catch-22

Users face an impossible choice:

**Option A: Narrow type definitions**
- Only match specific file patterns (e.g., `ADR-*.md`)
- Result: Many legitimate docs excluded → references fail

**Option B: Broad type definitions**
- Match all markdown files (e.g., `*.md`)
- Result: All docs included, BUT also validates:
  - `.claude/**/*.md` → 341 failures
  - `.venv/**/*.md` → 3 failures
  - `.git/**/*.md` → more failures
  - `node_modules/**/*.md` → even more failures

## Path Resolution Actually Works

Testing confirmed that `_resolve_by_file_path()` correctly handles:

```python
# Test 1: Subdirectory reference
source: roadmap/roadmap.md
target: ./milestones/milestone-0-hello-world.md
result: roadmap/milestones/milestone-0-hello-world.md ✓

# Test 2: Parent directory reference
source: specs/4-architecture/adrs/013-observability-stack.md
target: ../../../roadmap/milestones/milestone-0-hello-world.md
result: roadmap/milestones/milestone-0-hello-world.md ✓

# Test 3: Path.resolve() normalizes correctly
Path("fake/path/../does/not/exist.md").resolve()
→ /home/user/fake/does/not/exist.md ✓
```

The path construction and resolution logic is sound.

## Proposed Solution

### Option B: Directory Exclusion Support (RECOMMENDED)

Add support for excluding directories from validation, similar to other spec-check commands.

#### Part 1: Auto-exclude VCS Directories (Quick Win)

Automatically exclude common tool/VCS directories:
- `.git/`, `.hg/`, `.svn/`, `.bzr/`
- `.venv/`, `venv/`, `env/`
- `.claude/`
- `node_modules/`
- `__pycache__/`, `.pytest_cache/`

This matches the existing behavior in `spec_check/linter.py:221` (from PR #34).

#### Part 2: Add `--use-gitignore` Flag (Complete Solution)

Support `.gitignore` patterns for flexible exclusion:

```bash
# Default: respect .gitignore
spec-check validate-dsl specs/

# Disable gitignore
spec-check validate-dsl --no-gitignore specs/
```

Configuration via `pyproject.toml`:

```toml
[tool.spec-check.validate-dsl]
use_gitignore = true  # default
```

#### Implementation Details

**Location**: `spec_check/dsl/validator.py:189-207`

Current code:
```python
def validate(self, root_path: Path) -> ValidationResult:
    # ...
    # Find all markdown files
    markdown_files = list(root_path.rglob("*.md"))
```

Proposed change:
```python
def validate(self, root_path: Path, use_gitignore: bool = True) -> ValidationResult:
    # ...
    # Find all markdown files (respecting gitignore if enabled)
    markdown_files = self._find_markdown_files(root_path, use_gitignore)

def _find_markdown_files(self, root_path: Path, use_gitignore: bool) -> list[Path]:
    """Find markdown files, optionally respecting .gitignore patterns."""
    all_files = list(root_path.rglob("*.md"))

    # Always auto-exclude VCS directories
    filtered = [f for f in all_files if not self._is_vcs_directory(f)]

    if use_gitignore:
        # Load and apply .gitignore patterns
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern

        gitignore_patterns = self._load_gitignore_patterns(root_path)
        spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)
        filtered = [
            f for f in filtered
            if not spec.match_file(str(f.relative_to(root_path)))
        ]

    return filtered

def _is_vcs_directory(self, file_path: Path) -> bool:
    """Check if file is in a VCS or tool directory."""
    vcs_dirs = {'.git', '.hg', '.svn', '.bzr', '.venv', 'venv',
                '.claude', 'node_modules', '__pycache__', '.pytest_cache'}
    return any(part in vcs_dirs for part in file_path.parts)

def _load_gitignore_patterns(self, root_path: Path) -> list[str]:
    """Load patterns from .gitignore file."""
    gitignore_file = root_path / ".gitignore"
    if not gitignore_file.exists():
        return []

    patterns = []
    for line in gitignore_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            patterns.append(line)

    return patterns
```

**CLI changes** (`spec_check/cli.py:248-294`):

```python
def cmd_validate_dsl(args) -> int:
    """Execute the validate-dsl command."""
    # ...
    validator = DSLValidator(registry)
    result = validator.validate(root_path, use_gitignore=args.use_gitignore)
    # ...

# In argument parser setup:
validate_dsl_parser.add_argument(
    "--use-gitignore",
    action="store_true",
    default=True,
    help="Respect .gitignore patterns (default: enabled)"
)
validate_dsl_parser.add_argument(
    "--no-gitignore",
    action="store_false",
    dest="use_gitignore",
    help="Don't respect .gitignore patterns"
)
```

### Why This Solution is Best

1. **Solves the immediate problem**: Users can use broad type definitions without spurious errors
2. **Consistency**: Aligns with existing spec-check commands (`lint`, `check-links`)
3. **Backward compatible**: Can default to enabled without breaking usage
4. **CI-friendly**: `.gitignore` patterns already exist in most projects
5. **Low maintenance**: Reuses existing `pathspec` dependency

### Alternative Solutions (Rejected)

#### Option A: Fix File Path Resolution (NOT THE PROBLEM)

This was the original hypothesis but testing proved the resolution logic works correctly.

#### Option C: Explicit --exclude Flag

Could add `--exclude .claude --exclude .venv` but:
- `.gitignore` already exists and is standard
- Adds another configuration mechanism
- Less convenient than `.gitignore` patterns

## Testing Strategy

### Unit Tests

1. Test `_is_vcs_directory()` identifies VCS dirs
2. Test `_load_gitignore_patterns()` parses `.gitignore`
3. Test `_find_markdown_files()` with gitignore enabled/disabled

### Integration Tests

1. Create test structure with `.claude/` and `.venv/` directories
2. Verify these are auto-excluded even without `.gitignore`
3. Create `.gitignore` with custom patterns
4. Verify custom patterns are respected
5. Test `--no-gitignore` flag disables filtering

### Regression Tests

Ensure existing tests pass, particularly:
- `tests/test_dsl_coverage.py::test_file_path_reference_resolution`
- All ADR cross-reference tests

## Next Steps

1. Implement auto-exclude VCS directories (Part 1)
2. Add unit tests for VCS directory detection
3. Implement `.gitignore` support (Part 2)
4. Add CLI flags `--use-gitignore` / `--no-gitignore`
5. Update documentation and examples
6. Add integration tests
7. Update CHANGELOG.md

## References

- Issue #42: https://github.com/TradeMe/spec-check/issues/42
- PR #34: Auto-ignore VCS directories in linter
- PR #37: Support file path references in validate-dsl
- `spec_check/linter.py:221`: Existing VCS directory exclusion pattern
