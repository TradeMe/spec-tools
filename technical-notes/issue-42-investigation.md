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

## Proposed Solution (Revised)

### Three-Tier File Classification System

The solution introduces a three-tier classification for markdown files during validation:

1. **Excluded** - Files not scanned at all (via `.gitignore` and VCS auto-exclude)
2. **Typed** - Files matching type definitions (Job, ADR, Requirement, etc.)
3. **Unmanaged** - Files in scope but without strict validation (via `.specignore`)

This provides maximum flexibility while maintaining safety and clarity.

### Part 1: Auto-exclude VCS Directories (Safety)

Automatically exclude common tool/VCS directories during file scanning:
- `.git/`, `.hg/`, `.svn/`, `.bzr/`
- `.venv/`, `venv/`, `env/`
- `node_modules/`
- `__pycache__/`, `.pytest_cache/`

**Note**: `.claude/` is NOT auto-excluded since users may want to validate it.

This matches existing behavior in `spec_check/linter.py:221` (from PR #34).

### Part 2: Respect `.gitignore` for Complete Exclusion

Files matching `.gitignore` patterns are completely invisible to the validator (not scanned).

```bash
# Default: respect .gitignore
spec-check validate-dsl specs/

# Disable gitignore
spec-check validate-dsl --no-gitignore specs/
```

**Rationale**: `.gitignore` represents files truly out of scope (build artifacts, temp files, etc.).

### Part 3: Introduce `.specignore` for Unmanaged Files (NEW)

A new `.specignore` file marks files as "Unmanaged" type using gitignore-style glob patterns.

**Key distinction**:
- `.gitignore` → Files are invisible (not scanned)
- `.specignore` → Files are scanned and marked as "Unmanaged" type

**Example `.specignore`**:

```
# AI assistant context files (may want to validate these later)
.claude/**/*.md

# General documentation without formal structure
docs/notes/**/*.md
roadmap/**/*.md

# Meeting notes
meetings/**/*.md

# Developer guides
guides/**/*.md
```

### Unmanaged Type Concept

The "Unmanaged" type represents files that:
- ✅ Exist in the repository and are tracked by git
- ✅ Can be referenced from typed documents
- ✅ Are validated for existence when referenced
- ✅ Can reference other documents (typed or unmanaged)
- ❌ Don't have structural validation rules
- ❌ Don't require specific sections or IDs
- ❌ Don't participate in type checking

**Type Matching Precedence**:

When classifying a file, check in this order:
1. Does it match a specific type definition (Job, ADR, etc.)? → **Typed**
2. Does it match `.specignore` patterns? → **Unmanaged**
3. Otherwise → **Default behavior (see below)**

**Default behavior for unmatched files**:

Option A (RECOMMENDED): Auto-treat as Unmanaged
- Philosophy: "Everything is in scope by default"
- Users can gradually add type definitions as needed
- Low friction for getting started

Option B: Warning for unmatched files
- Encourages explicit classification
- Users must add to `.specignore` or create type definition
- More explicit but higher friction

### Reference Resolution with Unmanaged Types

When resolving a reference `[text](./other-doc.md)`:

1. **Try typed resolution first**:
   - Look up in ID registry by module ID or file path
   - If found, validate type matching if relationship specifies target type

2. **Fall back to unmanaged resolution**:
   - Check if file exists in unmanaged files registry
   - Validate file existence only
   - No type matching validation

3. **Error if neither**:
   - File not found in any registry
   - Typical "Module reference not found" error

**Example scenarios**:

```markdown
<!-- specs/architecture/ADR-011.md (Typed: ADR) -->
## Adheres To
- [Deployment Guide](../../docs/deployment.md)  ← Unmanaged, just check exists
- [ADR-010](./ADR-010.md)                        ← Typed, full validation

<!-- docs/deployment.md (Unmanaged) -->
## See Also
- [ADR-011](../specs/architecture/ADR-011.md)   ← Typed, full validation
- [Runbook](./runbook.md)                        ← Unmanaged, just check exists
```

#### Implementation Details

**File**: `spec_check/dsl/validator.py`

**New data structures**:

```python
@dataclass
class UnmanagedFile:
    """Represents an unmanaged markdown file."""
    file_path: Path
    """Path to the markdown file."""

class DSLValidator:
    def __init__(self, type_registry: SpecTypeRegistry):
        self.type_registry = type_registry
        self.id_registry = IDRegistry()
        self.unmanaged_files: dict[Path, UnmanagedFile] = {}  # NEW
        self.documents: dict[Path, DocumentContext] = {}
        # ...
```

**Modified validation flow**:

```python
def validate(self, root_path: Path, use_gitignore: bool = True,
             use_specignore: bool = True) -> ValidationResult:
    """Validate all markdown documents in a directory tree."""
    # Reset state
    self.id_registry = IDRegistry()
    self.unmanaged_files = {}
    self.documents = {}
    # ...

    # Find all markdown files (respecting .gitignore)
    markdown_files = self._find_markdown_files(root_path, use_gitignore)

    # Load .specignore patterns
    specignore_patterns = self._load_specignore_patterns(root_path) if use_specignore else []
    specignore_spec = None
    if specignore_patterns:
        from pathspec import PathSpec
        from pathspec.patterns import GitWildMatchPattern
        specignore_spec = PathSpec.from_lines(GitWildMatchPattern, specignore_patterns)

    # Pass 1 & 2: Parse documents and classify
    for file_path in markdown_files:
        self._process_and_classify_document(file_path, root_path, specignore_spec)

    # Pass 3: Type assignment and ID registration (only for typed docs)
    for doc_ctx in self.documents.values():
        self._assign_type_and_register(doc_ctx)

    # Pass 4-7: Existing validation passes...
    # ...

    # Pass 7: Reference resolution (modified to handle unmanaged)
    ref_resolver = ReferenceResolver(self.id_registry, self.unmanaged_files)
    # ...

def _process_and_classify_document(
    self, file_path: Path, root_path: Path, specignore_spec
) -> None:
    """Process document and classify as Typed or Unmanaged."""
    try:
        content = file_path.read_text()
        doc = parse_markdown_file(file_path)
        section_tree = build_section_tree(doc)

        # Try to match against type definitions
        module_def = self.type_registry.get_module_for_file(file_path)

        if module_def:
            # TYPED: Store for full validation
            self.documents[file_path] = DocumentContext(
                file_path=file_path,
                content=content,
                parsed_doc=doc,
                section_tree=section_tree,
            )
        else:
            # Check if matches .specignore patterns
            rel_path = file_path.relative_to(root_path)
            is_specignored = specignore_spec and specignore_spec.match_file(str(rel_path))

            # OPTION A: Auto-treat as unmanaged (recommended)
            # if is_specignored or True:  # Everything unmatched is unmanaged

            # OPTION B: Only specignored files are unmanaged
            if is_specignored:
                # UNMANAGED: Register but don't validate structure
                self.unmanaged_files[file_path] = UnmanagedFile(file_path=file_path)
            else:
                # Unmatched file - could warn/error/auto-treat as unmanaged
                # For now, treat as unmanaged (Option A)
                self.unmanaged_files[file_path] = UnmanagedFile(file_path=file_path)

    except Exception as e:
        self.errors.append(ValidationError(...))

def _find_markdown_files(self, root_path: Path, use_gitignore: bool) -> list[Path]:
    """Find markdown files, respecting .gitignore if enabled."""
    all_files = list(root_path.rglob("*.md"))

    # Always auto-exclude VCS directories (except .claude)
    filtered = [f for f in all_files if not self._is_vcs_directory(f)]

    if use_gitignore:
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
    # NOTE: .claude is NOT in this list - users may want to validate it
    vcs_dirs = {'.git', '.hg', '.svn', '.bzr', '.venv', 'venv', 'env',
                'node_modules', '__pycache__', '.pytest_cache'}
    return any(part in vcs_dirs for part in file_path.parts)

def _load_gitignore_patterns(self, root_path: Path) -> list[str]:
    """Load patterns from .gitignore file."""
    return self._load_ignore_patterns(root_path / ".gitignore")

def _load_specignore_patterns(self, root_path: Path) -> list[str]:
    """Load patterns from .specignore file."""
    return self._load_ignore_patterns(root_path / ".specignore")

def _load_ignore_patterns(self, file_path: Path) -> list[str]:
    """Load patterns from an ignore file."""
    if not file_path.exists():
        return []

    patterns = []
    for line in file_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            patterns.append(line)
    return patterns
```

**Reference resolver changes** (`spec_check/dsl/reference_resolver.py`):

```python
class ReferenceResolver:
    def __init__(self, registry: IDRegistry, unmanaged_files: dict[Path, UnmanagedFile] | None = None):
        self.registry = registry
        self.unmanaged_files = unmanaged_files or {}

    def _resolve_module_reference(
        self, reference: Reference, module_def: SpecModule | None
    ) -> ResolutionResult:
        """Resolve a module reference (link to another document by ID or path)."""
        target_id = self._extract_module_id(reference.link_target)

        if not target_id:
            return ResolutionResult(...)

        # Try typed resolution first
        target_module = self.registry.get_module(target_id)
        if not target_module and self._is_file_path(target_id):
            target_module = self._resolve_by_file_path(reference.source_file, target_id)

        if target_module:
            # TYPED: Full validation including type checking
            warning = None
            if module_def and reference.relationship:
                ref_def = self._find_reference_definition(module_def, reference.relationship)
                if ref_def and ref_def.target_type:
                    if target_module.module_type != ref_def.target_type:
                        warning = f"Type mismatch: expected {ref_def.target_type}, found {target_module.module_type}"

            return ResolutionResult(
                reference=reference,
                resolved=True,
                target_module=target_module,
                warning=warning,
            )

        # Fall back to unmanaged resolution
        if self._is_file_path(target_id):
            unmanaged_file = self._resolve_unmanaged_file(reference.source_file, target_id)
            if unmanaged_file:
                # UNMANAGED: Only check existence, no type validation
                return ResolutionResult(
                    reference=reference,
                    resolved=True,
                    # Note: Could add a flag to distinguish unmanaged resolution
                )

        # Not found in either registry
        suggestions = self._find_similar_module_ids(target_id)
        error_msg = f"Module reference '{target_id}' not found"
        if suggestions:
            error_msg += f". Did you mean: {', '.join(suggestions)}?"

        return ResolutionResult(reference=reference, resolved=False, error=error_msg)

    def _resolve_unmanaged_file(self, source_file: Path, target_path: str) -> UnmanagedFile | None:
        """Resolve reference to an unmanaged file."""
        if not target_path.endswith(".md"):
            target_path_with_ext = target_path + ".md"
        else:
            target_path_with_ext = target_path

        target_file = source_file.parent / target_path_with_ext

        # Look up in unmanaged files registry
        try:
            resolved_target = target_file.resolve()
            for unmanaged_path, unmanaged_file in self.unmanaged_files.items():
                if unmanaged_path.resolve() == resolved_target:
                    return unmanaged_file
        except (OSError, RuntimeError):
            pass

        return None
```

**CLI changes** (`spec_check/cli.py:248-294`):

```python
def cmd_validate_dsl(args) -> int:
    """Execute the validate-dsl command."""
    # ...
    validator = DSLValidator(registry)
    result = validator.validate(
        root_path,
        use_gitignore=args.use_gitignore,
        use_specignore=args.use_specignore
    )
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
validate_dsl_parser.add_argument(
    "--specignore",
    default=".specignore",
    help="Path to specignore file (default: .specignore)"
)
validate_dsl_parser.add_argument(
    "--no-specignore",
    action="store_false",
    dest="use_specignore",
    help="Don't use .specignore file"
)
```

### Why This Solution is Best

1. **Solves the immediate problem**: Files can be referenced without requiring full type definitions
2. **Flexible and evolutionary**: Start with `.specignore`, gradually move to typed specs
3. **Clear separation of concerns**:
   - `.gitignore` = completely out of scope
   - `.specignore` = in scope but unmanaged
   - Type definitions = fully validated
4. **Everything in scope by default**: Low friction for getting started
5. **Supports mixed documentation**: Formal specs alongside informal docs
6. **Type safety where it matters**: Typed → Typed references still validated
7. **Future-proof**: `.claude/` files can be validated when ready

### Benefits Over Original Proposal

The original proposal (just `.gitignore` support) had limitations:
- ❌ Binary choice: fully validate or completely ignore
- ❌ Can't reference general docs from typed specs
- ❌ All-or-nothing approach

The revised solution:
- ✅ Three tiers provide nuanced control
- ✅ Can reference any tracked file
- ✅ Gradual adoption path from unmanaged → typed
- ✅ Clear intent with separate `.specignore` file

## Testing Strategy

### Unit Tests

**File classification**:
1. Test `_is_vcs_directory()` identifies VCS dirs (but not `.claude`)
2. Test `_load_gitignore_patterns()` parses `.gitignore`
3. Test `_load_specignore_patterns()` parses `.specignore`
4. Test `_find_markdown_files()` with gitignore enabled/disabled
5. Test `_process_and_classify_document()` correctly classifies files as Typed/Unmanaged

**Reference resolution**:
1. Test typed → typed reference resolution (existing behavior)
2. Test typed → unmanaged reference resolution (new)
3. Test unmanaged → typed reference resolution (new)
4. Test unmanaged → unmanaged reference resolution (new)
5. Test type precedence: typed definition overrides specignore pattern

**Data structures**:
1. Test `UnmanagedFile` dataclass creation
2. Test unmanaged_files registry operations

### Integration Tests

**Scenario 1: VCS auto-exclusion**
```
project/
  .git/README.md          ← Excluded
  .venv/docs.md           ← Excluded
  node_modules/pkg.md     ← Excluded
  .claude/context.md      ← NOT excluded (can be validated)
  specs/ADR-001.md        ← Typed
```

**Scenario 2: Gitignore filtering**
```
project/
  .gitignore              # Contains: build/**
  build/output.md         ← Excluded by .gitignore
  specs/ADR-001.md        ← Typed
  docs/guide.md           ← Unmanaged
```

**Scenario 3: Specignore classification**
```
project/
  .specignore             # Contains: docs/**/*.md
  specs/ADR-001.md        ← Typed (matches ADR pattern)
  docs/guide.md           ← Unmanaged (matches .specignore)
  roadmap/plan.md         ← Unmanaged (no match, default behavior)
```

**Scenario 4: Type precedence**
```
project/
  .specignore             # Contains: specs/**/*.md
  specs/ADR-001.md        ← TYPED (type def takes precedence)
  specs/notes.md          ← Unmanaged (no type def, matches specignore)
```

**Scenario 5: Cross-tier references**
```
specs/ADR-011.md (Typed):
  - [Deployment Guide](../docs/deployment.md)  ← Unmanaged, succeeds
  - [ADR-010](./ADR-010.md)                     ← Typed, full validation

docs/deployment.md (Unmanaged):
  - [ADR-011](../specs/ADR-011.md)              ← Typed, succeeds
  - [Runbook](./runbook.md)                     ← Unmanaged, succeeds
```

**Scenario 6: Missing reference**
```
specs/ADR-011.md (Typed):
  - [Non-existent](./missing.md)                ← Error: not found
```

**Scenario 7: Everything in scope by default (Option A)**
```
project/
  # No .specignore file
  specs/ADR-001.md        ← Typed (matches pattern)
  docs/guide.md           ← Unmanaged (no match, auto-treat as unmanaged)
  random/notes.md         ← Unmanaged (no match, auto-treat as unmanaged)
```

### Regression Tests

Ensure existing tests pass, particularly:
- `tests/test_dsl_coverage.py::test_file_path_reference_resolution`
- All ADR cross-reference tests
- All existing validation tests

### CLI Tests

Test command-line flags:
1. `--use-gitignore` (default) vs `--no-gitignore`
2. `--specignore <path>` custom file location
3. `--no-specignore` disable specignore entirely
4. Combinations of flags

### Edge Cases

1. Empty `.specignore` file
2. `.specignore` with only comments
3. Circular references between typed and unmanaged files
4. File exists in both `.gitignore` and `.specignore` (gitignore wins)
5. Symlinks to markdown files
6. Non-existent files referenced from both typed and unmanaged docs

## Next Steps

### Phase 1: Core Infrastructure (Week 1)

1. **Add `UnmanagedFile` dataclass** to `validator.py`
2. **Implement VCS directory auto-exclusion** in `_is_vcs_directory()`
   - Exclude: `.git`, `.hg`, `.svn`, `.bzr`, `.venv`, `venv`, `env`, `node_modules`, `__pycache__`, `.pytest_cache`
   - Do NOT exclude: `.claude`
3. **Add `.gitignore` support** to `_find_markdown_files()`
4. **Add `.specignore` loading** via `_load_specignore_patterns()`
5. **Implement file classification** in `_process_and_classify_document()`
   - Type matching → Typed
   - Specignore pattern → Unmanaged
   - No match → Unmanaged (Option A: everything in scope by default)

### Phase 2: Reference Resolution (Week 2)

1. **Update `ReferenceResolver.__init__()`** to accept `unmanaged_files`
2. **Add `_resolve_unmanaged_file()`** method
3. **Modify `_resolve_module_reference()`** to fall back to unmanaged
4. **Update `ResolutionResult`** to distinguish unmanaged resolution
5. **Test type precedence**: typed lookup before unmanaged

### Phase 3: CLI Integration (Week 2)

1. **Add CLI flags**:
   - `--use-gitignore` / `--no-gitignore` (default: enabled)
   - `--specignore <path>` (default: `.specignore`)
   - `--no-specignore`
2. **Update `cmd_validate_dsl()`** to pass flags to validator
3. **Add `pyproject.toml` configuration support**:
   ```toml
   [tool.spec-check.validate-dsl]
   use_gitignore = true
   use_specignore = true
   specignore_file = ".specignore"
   ```

### Phase 4: Testing (Week 3)

1. **Write unit tests** for all new functions
2. **Write integration tests** for all 7 scenarios above
3. **Add regression tests** to ensure existing behavior unchanged
4. **Test CLI flags** with various combinations
5. **Test edge cases**

### Phase 5: Documentation (Week 3)

1. **Update README.md** with:
   - Explanation of three-tier system
   - `.specignore` usage guide
   - Examples of typed/unmanaged references
2. **Create `.specignore` example file**
3. **Update CLI help text**
4. **Add migration guide**: moving from old to new system
5. **Update CHANGELOG.md**

### Phase 6: Rollout (Week 4)

1. **Create pull request** with all changes
2. **Review and address feedback**
3. **Update version number** (minor version bump)
4. **Merge to main**
5. **Create GitHub release**
6. **Update issue #42** with solution details

## Decision Points

### Default Behavior for Unmatched Files

Two options for files that match neither a type definition nor `.specignore`:

**Option A: Auto-treat as Unmanaged (RECOMMENDED)**
- Philosophy: "Everything is in scope by default"
- Lower friction for getting started
- Users can gradually add type definitions
- No errors for having general docs in repo

**Option B: Warning for Unmatched Files**
- Encourages explicit classification
- Users must add to `.specignore` or create type definition
- More strict and explicit
- Higher friction but clearer intent

**Recommendation**: Start with Option A for low friction. Can add a `--strict` flag later that enables Option B behavior.

### Reporting Unmanaged File Statistics

Should validation report include unmanaged file counts?

```
Validation PASSED: 0 errors, 0 warnings, 3 info messages
Documents validated: 13
  - Typed: 10
  - Unmanaged: 3
References validated: 25
  - Typed → Typed: 15
  - Typed → Unmanaged: 5
  - Unmanaged → Typed: 3
  - Unmanaged → Unmanaged: 2
```

**Recommendation**: Yes, include statistics for visibility and debugging.

## References

- Issue #42: https://github.com/TradeMe/spec-check/issues/42
- PR #34: Auto-ignore VCS directories in linter
- PR #37: Support file path references in validate-dsl
- `spec_check/linter.py:221`: Existing VCS directory exclusion pattern
