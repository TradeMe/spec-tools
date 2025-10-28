# Publishing spec-check to PyPI

This document explains how to publish spec-check to PyPI using our automated release workflows.

## Overview

The project uses a fully automated publishing system with multiple safeguards:

- **Automatic TestPyPI Publishing**: Every merge to `main` automatically publishes a dev version to TestPyPI
- **Version Control Enforcement**: CI checks prevent version changes outside the release process
- **Release Workflow**: Automated workflow prepares release PRs with proper version and changelog updates
- **Trusted Publishing**: Uses OIDC for secure authentication (no API tokens needed)

## Publishing Workflows

### 1. Development Versions (Automatic)

Every merge to `main` automatically:
- Creates a development version (e.g., `0.1.0.dev123+abc1234`)
- Publishes to TestPyPI
- Comments on the PR with installation instructions

No manual action required! This allows immediate testing of merged changes.

**Installation:**
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-check
```

**Note:** The package name on PyPI is `spec-check` (not `spec-check`) due to a name collision.

### 2. Official Releases

Official releases use a Claude Code-assisted process with full automation.

#### The Process (Your Steps)

**You do exactly 2 things:**

1. **Request a release** in a Claude Code session:
   ```
   "Make a release for version 0.2.0"
   ```
   or just:
   ```
   "Make a release"
   ```

2. **Merge the PR** that Claude creates (after reviewing it)

That's it! Everything else is automated.

#### What Happens Behind the Scenes

**Claude Code does:**
- ✅ Updates `pyproject.toml` with the new version
- ✅ Updates `CHANGELOG.md` with the release date
- ✅ Moves unreleased changes to the version section
- ✅ Creates a release branch (`release/v0.2.0`)
- ✅ Commits the changes with proper message
- ✅ Creates a PR labeled with `release`
- ✅ Adds a comprehensive PR description

**After you merge the PR:**
- ✅ GitHub release is automatically created with tag `v0.2.0`
- ✅ Release notes are extracted from `CHANGELOG.md`
- ✅ Package is automatically built and published to PyPI in the same workflow
- ✅ Pre-release flag is set for alpha/beta/rc versions
- ✅ PR receives a comment when publishing completes successfully

**The only manual step is reviewing and merging the PR! Everything else is fully automated.**

#### Example Session

```
You: "Make a release for version 0.2.0"

Claude: ✅ Release PR created: https://github.com/TradeMe/spec-check/pull/123

Next steps:
1. Review the PR (especially CHANGELOG.md)
2. Wait for CI to pass
3. Merge the PR

After merge, automatically:
- GitHub release created
- Package published to PyPI
- Installation: pip install --upgrade spec-check

You: *reviews and merges PR*

[GitHub Actions automatically creates release, builds package, and publishes to PyPI - all in one workflow]
```

## Version Enforcement

The project prevents accidental version changes with CI checks:

### Version Check Workflow

Runs on every PR that modifies `pyproject.toml`:

- ❌ **Blocks** version changes without the `release` label
- ✅ **Validates** version format (semantic versioning)
- ✅ **Requires** `CHANGELOG.md` to be updated

**To bypass (not recommended):**
- Add the `release` label to your PR
- Only do this for emergency hotfixes or special cases

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0): Incompatible API changes
- **MINOR** version (0.1.0): New functionality, backwards compatible
- **PATCH** version (0.0.1): Bug fixes, backwards compatible

**Pre-release versions:**
- Alpha: `0.2.0-alpha.1`
- Beta: `0.2.0-beta.1`
- Release Candidate: `0.2.0-rc.1`

**Development versions (automatic):**
- `0.1.0.dev123+abc1234` (automatically generated from commit count and hash)

## Prerequisites (One-Time Setup)

### 1. Set up PyPI Trusted Publishing

**For PyPI (production releases):**

1. Go to [PyPI](https://pypi.org) and log in
2. Navigate to your account settings → Publishing
3. Add a new "pending publisher" with these details:
   - **PyPI Project Name**: `spec-check`
   - **Owner**: `TradeMe`
   - **Repository name**: `spec-check`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

**For TestPyPI (automatic dev versions):**

1. Go to [TestPyPI](https://test.pypi.org) and log in
2. Navigate to your account settings → Publishing
3. Add a new "pending publisher" with the same details as above, but use:
   - **Environment name**: `testpypi`

### 2. Configure GitHub Environments

1. Go to your GitHub repository → Settings → Environments
2. Create two environments:
   - **pypi**: For production releases to PyPI
   - **testpypi**: For test releases to TestPyPI
3. (Optional) Add protection rules to `pypi`:
   - Require reviewers before deployment
   - Restrict to specific branches (e.g., `main`)

### 3. Create the `release` Label

1. Go to Issues → Labels
2. Create a new label:
   - **Name**: `release`
   - **Description**: Marks PRs that are allowed to change the version
   - **Color**: Your choice (suggest: purple or gold)

## Changelog Management

We use [Keep a Changelog](https://keepachangelog.com/) format.

### During Development

Add changes to the `[Unreleased]` section as you make them:

```markdown
## [Unreleased]

### Added
- New feature X

### Changed
- Modified behavior of Y

### Fixed
- Bug in Z
```

### During Release

The "Prepare Release" workflow automatically:
- Moves `[Unreleased]` content to a versioned section
- Adds the release date
- Updates version links at the bottom

**No manual changelog editing needed for releases!**

## Testing Releases

### Test a Development Version

After merging any PR to `main`:

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-check

# Verify version (command is still spec-check)
spec-check --version
```

### Test a Release Before Publishing

After merging a release PR:

```bash
# Install the dev version that was just published
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-check==<version>.devXXX

# Run tests (command is still spec-check)
spec-check lint
spec-check check-coverage
```

If everything looks good, proceed with creating the GitHub release.

## Alternative: Manual Workflow (Without Claude)

If you need to create a release without Claude Code, you can use the manual workflow:

1. Go to **Actions** → **Prepare Release** → **Run workflow**
2. Enter the version number
3. Review and merge the PR it creates
4. The release is automatically created and published

This is functionally equivalent to the Claude-assisted process, just requires clicking through the GitHub UI.

## Manual Publishing (Emergency Only)

If automated publishing fails completely, you can publish manually:

1. **Install build tools**:
   ```bash
   uv sync --extra dev
   ```

2. **Update version and changelog manually**:
   - Edit `pyproject.toml`
   - Edit `CHANGELOG.md`
   - Commit changes

3. **Build the package**:
   ```bash
   uv run flit build
   ```

4. **Install twine**:
   ```bash
   uv pip install twine
   ```

5. **Check the distribution**:
   ```bash
   uv run twine check dist/*
   ```

6. **Publish to PyPI**:
   ```bash
   uv run twine upload dist/*
   ```

   You'll need a PyPI API token. Create one at https://pypi.org/manage/account/token/

## Pre-Release Checklist

Before running "Prepare Release":

- [ ] All features for this release are merged to `main`
- [ ] All tests passing on `main`
- [ ] All linters passing on `main`
- [ ] `CHANGELOG.md` has all changes documented in `[Unreleased]`
- [ ] Documentation is up to date
- [ ] Version number follows semantic versioning

## Post-Release Tasks

After publishing a release:

1. **Verify installation**:
   ```bash
   pip install --upgrade spec-check
   spec-check --version  # Command is still spec-check
   ```

2. **Check PyPI page**:
   - Visit https://pypi.org/project/spec-check/
   - Verify metadata, description, and links are correct

3. **Update GitHub milestones** (if used):
   - Close the milestone for this release
   - Create a milestone for the next release

4. **Announce the release** (optional):
   - Share release notes on relevant channels
   - Update external documentation

## Common Workflows

### Release a Patch Version (Bug Fix)

```
You: "Make a release for version 0.1.1"
Claude: [creates PR]
You: [merge PR]
System: [auto-creates release and publishes]
```

### Release a Minor Version (New Features)

```
You: "Make a release for version 0.2.0"
Claude: [creates PR]
You: [merge PR]
System: [auto-creates release and publishes]
```

### Release a Pre-release (Alpha/Beta)

```
You: "Make a release for version 0.2.0-alpha.1"
Claude: [creates PR]
You: [merge PR]
System: [auto-creates release as pre-release and publishes]
```

Pre-release versions are automatically detected and marked appropriately.

## Troubleshooting

### Build Fails

- Check that all tests pass locally: `uv run pytest tests/ -v`
- Ensure `pyproject.toml` is valid
- Verify all required files are included

### Publishing Fails

**Trusted Publishing (OIDC) errors:**
- Verify the PyPI trusted publisher is configured correctly
- Check that the workflow name and environment match exactly
- Ensure the GitHub environment exists and has correct permissions
- Check the workflow logs for specific error messages

**Version conflicts:**
- You cannot republish the same version to PyPI
- For development versions, the commit hash makes each unique
- For releases, increment the version number

**Release created but package not published:**
- This should not happen with the current workflow (post v0.1.0)
- The workflow now builds and publishes in a single job chain
- If you see this, check the workflow run logs for errors
- Verify the `pypi` environment is configured in GitHub settings

### Version Check Fails on PR

This is expected! Version changes are only allowed through the release process:

**Solutions:**
- Use the "Prepare Release" workflow for releases
- If you need to change version for other reasons, add the `release` label
- Revert the version change if it was accidental

### CHANGELOG Not Updated

The version check requires changelog updates for releases:

**Solution:**
- Add your changes to the `[Unreleased]` section in `CHANGELOG.md`
- The "Prepare Release" workflow will move them to the versioned section

## Additional Resources

- [Keep a Changelog](https://keepachangelog.com/)
- [Semantic Versioning](https://semver.org/)
- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
