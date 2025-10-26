# Publishing spec-tools to PyPI

This document explains how to publish spec-tools to PyPI.

## Overview

The project uses automated publishing via GitHub Actions with PyPI Trusted Publishing (OIDC). This is the recommended and most secure method for publishing packages.

## Prerequisites

### 1. Set up PyPI Trusted Publishing

**For PyPI (production releases):**

1. Go to [PyPI](https://pypi.org) and log in
2. Navigate to your account settings → Publishing
3. Add a new "pending publisher" with these details:
   - **PyPI Project Name**: `spec-tools`
   - **Owner**: `TradeMe` (GitHub organization/user)
   - **Repository name**: `spec-tools`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi`

**For TestPyPI (testing):**

1. Go to [TestPyPI](https://test.pypi.org) and log in
2. Navigate to your account settings → Publishing
3. Add a new "pending publisher" with the same details as above, but use:
   - **Environment name**: `testpypi`

### 2. Configure GitHub Environments

1. Go to your GitHub repository → Settings → Environments
2. Create two environments:
   - **pypi**: For production releases to PyPI
   - **testpypi**: For test releases to TestPyPI
3. (Optional) Add protection rules:
   - Require reviewers before deployment
   - Restrict to specific branches (e.g., `main`)

## Publishing Workflow

### Automated Publishing (Recommended)

#### Publishing to PyPI (Production)

1. **Ensure all tests pass**:
   ```bash
   uv run pytest tests/ -v --cov
   uv run ruff check spec_tools/ tests/
   uv run ruff format --check spec_tools/ tests/
   ```

2. **Update version** in `pyproject.toml`:
   ```toml
   version = "0.2.0"  # Update to new version
   ```

3. **Commit and push changes**:
   ```bash
   git add pyproject.toml
   git commit -m "chore: Bump version to 0.2.0"
   git push
   ```

4. **Create a GitHub Release**:
   - Go to GitHub → Releases → Create a new release
   - Create a new tag (e.g., `v0.2.0`)
   - Write release notes describing changes
   - Click "Publish release"

5. **Monitor the workflow**:
   - The `publish.yml` workflow will automatically trigger
   - It will build, test, and publish to PyPI
   - Check the Actions tab for progress

#### Testing with TestPyPI

To test the publishing process before making a production release:

1. Go to GitHub Actions → Publish to PyPI workflow
2. Click "Run workflow"
3. Check "Publish to TestPyPI instead of PyPI"
4. Click "Run workflow"

This allows you to verify the package builds and publishes correctly without affecting the production PyPI package.

### Manual Publishing

If you need to publish manually (not recommended for production):

1. **Install build tools**:
   ```bash
   uv pip install flit twine
   ```

2. **Build the package**:
   ```bash
   uv run flit build
   ```

   This creates distribution files in the `dist/` directory:
   - `spec_tools-<version>.tar.gz` (source distribution)
   - `spec_tools-<version>-py3-none-any.whl` (wheel)

3. **Check the distribution**:
   ```bash
   uv run twine check dist/*
   ```

4. **Publish to TestPyPI** (optional, for testing):
   ```bash
   uv run twine upload --repository testpypi dist/*
   ```

   You'll need a TestPyPI API token. Create one at https://test.pypi.org/manage/account/token/

5. **Test installation from TestPyPI**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-tools
   ```

6. **Publish to PyPI**:
   ```bash
   uv run twine upload dist/*
   ```

   You'll need a PyPI API token. Create one at https://pypi.org/manage/account/token/

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0): Incompatible API changes
- **MINOR** version (0.1.0): New functionality, backwards compatible
- **PATCH** version (0.0.1): Bug fixes, backwards compatible

Examples:
- `0.1.0` → `0.1.1`: Bug fix
- `0.1.0` → `0.2.0`: New feature
- `0.9.0` → `1.0.0`: First stable release or breaking changes

## Pre-Release Checklist

Before publishing a new version:

- [ ] All tests pass (`uv run pytest tests/ -v`)
- [ ] All linters pass (`uv run ruff check && uv run ruff format --check`)
- [ ] Project linters pass (if applicable to changes):
  - [ ] `uv run spec-tools lint`
  - [ ] `uv run spec-tools check-structure`
  - [ ] `uv run spec-tools check-coverage`
  - [ ] `uv run spec-tools check-schema`
- [ ] Version number updated in `pyproject.toml`
- [ ] README.md is up to date
- [ ] CHANGELOG or release notes prepared
- [ ] All changes committed and pushed
- [ ] (Optional) Test with TestPyPI first

## Post-Release Tasks

After a successful release:

1. **Verify installation**:
   ```bash
   pip install --upgrade spec-tools
   spec-tools --help
   ```

2. **Check PyPI page**:
   - Visit https://pypi.org/project/spec-tools/
   - Verify metadata, description, and links are correct

3. **Announce the release** (optional):
   - Update documentation
   - Post on relevant channels
   - Share release notes

## Troubleshooting

### Build Fails

- Check that all tests pass locally
- Ensure `pyproject.toml` is valid
- Verify all required files are included

### Publishing Fails

**Trusted Publishing (OIDC) errors:**
- Verify the PyPI trusted publisher is configured correctly
- Check that the workflow name and environment match exactly
- Ensure the GitHub environment exists and has correct permissions

**Authentication errors (manual publishing):**
- Generate a new API token
- Use `__token__` as the username
- Paste the token (including `pypi-` prefix) as the password

**Version conflicts:**
- You cannot republish the same version
- Increment the version number in `pyproject.toml`
- Delete local `dist/` directory before rebuilding

### Package Not Found After Publishing

- Wait a few minutes for PyPI to update its index
- Try `pip install --upgrade spec-tools`
- Check the PyPI page to confirm it's published

## Additional Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions PyPI Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Flit Documentation](https://flit.pypa.io/)
