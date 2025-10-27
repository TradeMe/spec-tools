# GitHub Actions Workflows

This directory contains all CI/CD workflows for spec-check.

## Workflows Overview

### `ci.yml` - Continuous Integration
**Triggers:** Push to `main` and `claude/*` branches, PRs to `main`

**Purpose:** Run tests and linters on all code changes

**Jobs:**
- **test**: Runs pytest on Python 3.10, 3.11, 3.12, 3.13 with coverage
- **lint**: Runs ruff check/format and all spec-check linters

**When it fails:** Fix the code - all checks must pass before merging

---

### `version-check.yml` - Version Control Enforcement
**Triggers:** PRs to `main` that modify `pyproject.toml`

**Purpose:** Prevent unauthorized version changes outside the release process

**Checks:**
- ❌ Blocks version changes without `release` label
- ✅ Validates semantic versioning format
- ✅ Requires CHANGELOG.md to be updated

**When it fails:**
- If you're making a release: Use Claude Code or the "Prepare Release" workflow
- If version changed accidentally: Revert the change
- For emergency hotfixes: Add the `release` label manually

**Bypass:** Add the `release` label to the PR (only for release PRs!)

---

### `publish.yml` - PyPI Publishing
**Triggers:**
- Push to `main` (publishes dev version to TestPyPI)
- GitHub release published (publishes to PyPI)
- Manual workflow dispatch (choose TestPyPI or PyPI)

**Purpose:** Build and publish packages to PyPI and TestPyPI

**Jobs:**
1. **build**: Runs tests, linters, builds distribution packages
2. **publish-to-pypi**: Publishes to PyPI (only for GitHub releases)
3. **publish-to-testpypi**: Publishes to TestPyPI (for main pushes and manual dispatch)

**Version handling:**
- GitHub releases: Uses version from `pyproject.toml` as-is
- Main branch pushes: Creates dev version `0.1.0.dev123+abc1234`

**Authentication:** Uses PyPI Trusted Publishing (OIDC) - no API tokens needed

**When it fails:**
- Check build logs for test/lint failures
- Verify PyPI trusted publisher configuration
- Check GitHub environment permissions

---

### `prepare-release.yml` - Manual Release Preparation
**Triggers:** Manual workflow dispatch

**Purpose:** Alternative to Claude Code for preparing release PRs

**Use this when:**
- Claude Code is not available
- You prefer the GitHub UI
- You want to prepare a release manually

**What it does:**
1. Validates version format
2. Updates `pyproject.toml` with new version
3. Updates `CHANGELOG.md` with release date
4. Creates a release branch
5. Creates a PR with `release` label

**Inputs:**
- `version`: The version to release (e.g., `0.2.0`, `1.0.0-alpha.1`)

**How to use:**
1. Actions → Prepare Release → Run workflow
2. Enter version number
3. Review and merge the PR it creates
4. Release is automatically created and published

---

### `create-release.yml` - Automatic Release Creation
**Triggers:** PR with `release` label merged to `main`

**Purpose:** Automatically create GitHub releases when release PRs are merged

**What it does:**
1. Extracts version from `pyproject.toml`
2. Extracts release notes from `CHANGELOG.md`
3. Creates GitHub release with tag `vX.Y.Z`
4. Marks as pre-release if version contains `-alpha`, `-beta`, or `-rc`
5. Comments on the PR with release link

**When this runs:**
- After merging a Claude-created release PR
- After merging a prepare-release.yml PR

**What happens next:**
- GitHub release triggers `publish.yml`
- Package is published to PyPI
- Users can install with `pip install spec-check`

---

## Workflow Relationships

```
┌─────────────────────────────────────────────────────────────┐
│ Development Flow (Automatic)                                 │
└─────────────────────────────────────────────────────────────┘

PR created → ci.yml runs (tests + lints)
    ↓
PR merged to main → ci.yml runs (tests + lints)
    ↓                    ↓
    └─────→ publish.yml publishes dev version to TestPyPI
                         ↓
            Comment added to PR with install instructions


┌─────────────────────────────────────────────────────────────┐
│ Release Flow (Claude Code - Recommended)                     │
└─────────────────────────────────────────────────────────────┘

User: "Make a release for 0.2.0"
    ↓
Claude: Updates pyproject.toml + CHANGELOG.md
    ↓
Claude: Creates release PR with "release" label
    ↓
version-check.yml: ✅ Allows change (has "release" label)
    ↓
ci.yml: ✅ Tests + lints pass
    ↓
User: Merges PR
    ↓
create-release.yml: Creates GitHub release v0.2.0
    ↓                    ↓
    │         Extracts notes from CHANGELOG.md
    ↓                    ↓
publish.yml: Publishes to PyPI
    ↓
Package available: pip install spec-check


┌─────────────────────────────────────────────────────────────┐
│ Release Flow (Manual Alternative)                            │
└─────────────────────────────────────────────────────────────┘

User: Actions → Prepare Release → Enter version
    ↓
prepare-release.yml: Creates release PR with "release" label
    ↓
version-check.yml: ✅ Allows change (has "release" label)
    ↓
ci.yml: ✅ Tests + lints pass
    ↓
User: Merges PR
    ↓
create-release.yml: Creates GitHub release
    ↓
publish.yml: Publishes to PyPI
```

## Environment Requirements

### GitHub Environments

Two environments must be configured in GitHub Settings:

1. **pypi**
   - Used for production releases
   - Recommended: Enable required reviewers
   - Recommended: Restrict to `main` branch

2. **testpypi**
   - Used for dev versions and testing
   - No restrictions needed

### PyPI Trusted Publishers

Must be configured on both PyPI and TestPyPI:

- Project name: `spec-check`
- Repository: `TradeMe/spec-check`
- Workflow: `publish.yml`
- Environments: `pypi` and `testpypi`

See [PYPI_SETUP.md](../../PYPI_SETUP.md) for detailed setup instructions.

### GitHub Labels

One label must exist:

- **release**: Marks PRs that change the version
  - Allows bypass of version-check.yml
  - Triggers create-release.yml on merge

## Common Tasks

### Run tests locally
```bash
uv run pytest tests/ -v
uv run ruff check spec_check/ tests/
uv run ruff format --check spec_check/ tests/
```

### Prepare a release (Claude Code)
```
"Make a release for version 0.2.0"
```

### Prepare a release (Manual)
1. Actions → Prepare Release → Run workflow
2. Enter version
3. Merge the PR

### Publish to TestPyPI manually
1. Actions → Publish → Run workflow
2. Select "testpypi"

### Check why a workflow failed
1. Actions → Click failed workflow
2. Click failed job
3. Expand failed step
4. Check error message

## Security

All workflows use:
- **Least privilege permissions**: Only what's needed
- **Trusted Publishing (OIDC)**: No API tokens
- **Environment protection**: Manual approval for PyPI
- **Branch protection**: Prevents direct pushes to main

## Maintenance

When updating workflows:

1. **Test in a PR first** - workflows run on PRs
2. **Check the logs** - verify everything works
3. **Update this README** - keep documentation current
4. **Update PUBLISHING.md** - if user-facing changes

## Troubleshooting

### Workflow not triggering

- Check the trigger conditions in the workflow file
- Verify branch names match
- Check if paths filter is excluding your changes

### Permission denied

- Check workflow permissions (Settings → Actions → General)
- Verify environment permissions exist
- Check if GITHUB_TOKEN has required scopes

### Environment not found

- Create in Settings → Environments
- Name must match exactly (case-sensitive)
- Re-run workflow after creating

### Trusted publishing failed

- Verify PyPI trusted publisher configuration
- Check repository name matches exactly
- Ensure workflow name is `publish.yml`
- Verify environment name matches
