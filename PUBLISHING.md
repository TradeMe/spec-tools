# Publishing spec-tools to PyPI

This document explains how to publish spec-tools to PyPI using our automated release workflows.

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
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-tools
```

### 2. Official Releases

Official releases follow a structured process enforced by CI:

#### Step 1: Prepare Release

Use the "Prepare Release" workflow to create a release PR:

1. Go to **Actions** → **Prepare Release** → **Run workflow**
2. Enter the version number (e.g., `0.2.0`, `1.0.0-alpha.1`)
3. Click **Run workflow**

The workflow will:
- ✅ Validate the version format (semantic versioning)
- ✅ Check the version doesn't already exist
- ✅ Update `pyproject.toml` with the new version
- ✅ Update `CHANGELOG.md` with the release date
- ✅ Create a release branch (`release/v0.2.0`)
- ✅ Create a PR labeled with `release`
- ✅ Populate the PR with a release checklist

#### Step 2: Review and Merge

1. Review the automatically created release PR
2. Verify all CI checks pass
3. Merge the PR

**After merging:**
- A dev version is published to TestPyPI for final testing

#### Step 3: Create GitHub Release

1. Go to **Releases** → **Draft a new release**
2. Create a new tag matching the version (e.g., `v0.2.0`)
3. Set the release title to the version (e.g., `v0.2.0`)
4. Copy release notes from `CHANGELOG.md`
5. Click **Publish release**

**After publishing:**
- The official version is automatically published to PyPI
- The package is available via `pip install spec-tools`

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
   - **PyPI Project Name**: `spec-tools`
   - **Owner**: `TradeMe`
   - **Repository name**: `spec-tools`
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
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-tools

# Verify version
spec-tools --version
```

### Test a Release Before Publishing

After merging a release PR:

```bash
# Install the dev version that was just published
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-tools==<version>.devXXX

# Run tests
spec-tools lint
spec-tools check-coverage
```

If everything looks good, proceed with creating the GitHub release.

## Manual Publishing (Emergency Only)

If automated publishing fails, you can publish manually:

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
   pip install --upgrade spec-tools
   spec-tools --version
   ```

2. **Check PyPI page**:
   - Visit https://pypi.org/project/spec-tools/
   - Verify metadata, description, and links are correct

3. **Update GitHub milestones** (if used):
   - Close the milestone for this release
   - Create a milestone for the next release

4. **Announce the release** (optional):
   - Share release notes on relevant channels
   - Update external documentation

## Common Workflows

### Release a Patch Version (Bug Fix)

```bash
# 1. Run Prepare Release workflow with version 0.1.1
# 2. Review and merge the PR
# 3. Create GitHub release with tag v0.1.1
```

### Release a Minor Version (New Features)

```bash
# 1. Run Prepare Release workflow with version 0.2.0
# 2. Review and merge the PR
# 3. Create GitHub release with tag v0.2.0
```

### Release a Pre-release (Alpha/Beta)

```bash
# 1. Run Prepare Release workflow with version 0.2.0-alpha.1
# 2. Review and merge the PR
# 3. Create GitHub release with tag v0.2.0-alpha.1
# 4. Mark the release as "pre-release" on GitHub
```

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
