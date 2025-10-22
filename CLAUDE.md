# Claude Development Guidelines

This document provides guidelines for AI-assisted development sessions on this project to maintain code quality and prevent CI failures.

## Critical: Run All Linters Before Pushing

**Always run these commands before committing and pushing:**

```bash
# 1. Run ruff linting
ruff check spec_tools/ tests/

# 2. Run ruff formatting (this is the most commonly missed step!)
ruff format spec_tools/ tests/

# 3. Run tests
python -m pytest tests/ -v

# 4. Run all project linters
python -m spec_tools lint --verbose
python -m spec_tools check-structure
python -m spec_tools check-coverage
python -m spec_tools check-schema
```

### Quick Pre-Push Check

Run this single command to catch most issues:

```bash
ruff check spec_tools/ tests/ && \
ruff format --check spec_tools/ tests/ && \
python -m pytest tests/ -q && \
echo "✅ All checks passed!"
```

If `ruff format --check` fails, run `ruff format spec_tools/ tests/` to fix formatting issues.

## Python Version Requirements

- **Minimum**: Python 3.10
- **Tested on**: Python 3.10, 3.11, 3.12, 3.13
- **Type hints**: Use modern syntax (e.g., `list[str]` not `List[str]`, `X | None` not `Optional[X]`)

## Code Style Guidelines

### Type Annotations

Use Python 3.10+ native type annotations:

✅ **Correct:**
```python
def process(items: list[str]) -> dict[str, int]:
    """Process items."""
    return {"count": len(items)}

def find(key: str) -> str | None:
    """Find item."""
    return items.get(key)
```

❌ **Incorrect:**
```python
from typing import List, Dict, Optional

def process(items: List[str]) -> Dict[str, int]:  # Don't use typing.List/Dict
    return {"count": len(items)}

def find(key: str) -> Optional[str]:  # Don't use Optional
    return items.get(key)
```

### Line Length

- Maximum 100 characters per line
- If a line is too long, split it logically:

```python
# Good - split at natural boundaries
lines.append(
    f"Tests: {self.tests_with_requirements}/{self.total_tests} "
    f"linked to requirements"
)
```

### Imports

Remove unused imports. Ruff will flag these automatically.

## Project Structure

### Linters

The project provides five linters:

1. **`lint`** - File allowlist validation
2. **`check-links`** - Markdown link validation
3. **`check-coverage`** - Spec-to-test traceability validation
4. **`check-structure`** - Spec-to-test structure validation
5. **`check-schema`** - Markdown schema validation

### Test Organization

- Tests use pytest markers to link to requirements: `@pytest.mark.req("REQ-001")`
- Test files should match spec files: `specs/feature.md` → `tests/test_feature.py`
- Unit tests without spec links are allowed (for implementation details)

## Common Issues and Solutions

### Issue: Ruff Format Failures in CI

**Symptom:** CI fails with "Would reformat: ..." messages

**Solution:**
```bash
# Always run BOTH ruff commands:
ruff check --fix spec_tools/ tests/
ruff format spec_tools/ tests/
```

### Issue: Type Annotation Errors

**Symptom:** `UP035`, `UP045`, or `UP006` errors from ruff

**Solution:** Use Python 3.10+ native types:
- `list[X]` instead of `List[X]`
- `dict[K, V]` instead of `Dict[K, V]`
- `X | None` instead of `Optional[X]`
- `tuple[X, Y]` instead of `Tuple[X, Y]`

### Issue: Import Errors

**Symptom:** `F401` errors about unused imports

**Solution:** Remove the unused imports. Ruff can fix these automatically:
```bash
ruff check --fix spec_tools/ tests/
```

## CI/CD Pipeline

The CI runs the following checks:

**Tests:**
- pytest on Python 3.10, 3.11, 3.12, 3.13
- Coverage reporting

**Linting:**
- `ruff check` (code quality)
- `ruff format --check` (formatting)
- `spec-tools lint` (file allowlist)
- `spec-tools check-structure` (spec-test structure)
- `spec-tools check-coverage` (requirement coverage)
- `spec-tools check-schema` (markdown schema)

All of these must pass for CI to succeed.

## Git Workflow

### Branch Naming

Use descriptive branch names prefixed with `claude/`:
```
claude/add-feature-name-<session-id>
```

### Commit Messages

Use conventional commit format with the Claude signature:

```
<type>: <description>

<body - explain what and why>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Before Pushing

**Critical checklist:**
- [ ] Run `ruff check spec_tools/ tests/`
- [ ] Run `ruff format spec_tools/ tests/`
- [ ] Run `python -m pytest tests/ -v`
- [ ] Run project linters if relevant to changes
- [ ] Verify all checks pass

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_linter.py -v

# Run with coverage
python -m pytest tests/ -v --cov=spec_tools --cov-report=term-missing

# Quick run (quiet mode)
python -m pytest tests/ -q
```

### Writing Tests

- Use descriptive test names: `test_<what>_<condition>_<expected>`
- Add pytest markers for requirement tests: `@pytest.mark.req("REQ-001")`
- Use `tmp_path` fixture for file system tests
- Follow existing test patterns in the codebase

## Documentation

- Update README.md when adding new features
- Document CLI commands with comprehensive help text
- Add docstrings to all public functions and classes
- Include examples in epilog text for CLI commands

## Merging Changes

When merging branches:
1. Fetch and merge main first: `git fetch origin main && git merge origin/main`
2. Resolve conflicts carefully, preserving all features
3. Run full linter suite after merge
4. Fix any ruff formatting issues: `ruff format spec_tools/ tests/`
5. Run tests to verify merge: `python -m pytest tests/ -v`
6. Commit merge with descriptive message

## Session End Checklist

Before ending a development session:
- [ ] All tests passing
- [ ] All linters passing (especially ruff format!)
- [ ] Changes committed with descriptive messages
- [ ] Changes pushed to remote branch
- [ ] CI checks started (verify in GitHub Actions)

## Questions or Issues?

If you encounter issues not covered here:
1. Check the CI logs for detailed error messages
2. Review similar tests in the codebase
3. Consult the project README.md
4. Check Python 3.10+ documentation for type hint syntax
