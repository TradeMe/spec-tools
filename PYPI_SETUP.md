# PyPI Setup Guide

This guide walks through the one-time manual setup required before spec-tools can be published to PyPI.

## Overview

You need to configure:
1. PyPI Trusted Publishing (for production releases)
2. TestPyPI Trusted Publishing (for dev versions and testing)
3. GitHub Environments
4. GitHub Labels

**Time required:** ~10-15 minutes

## Step 1: Set Up PyPI Trusted Publishing

### 1.1 Create PyPI Account

If you don't have one:
1. Go to https://pypi.org/account/register/
2. Create your account
3. Verify your email

### 1.2 Configure Trusted Publisher for PyPI

1. Go to https://pypi.org and log in
2. Click your username → **Account settings**
3. Scroll to **Publishing** section
4. Click **Add a new pending publisher**

Fill in these details:
```
PyPI Project Name:    spec-tools
Owner:                TradeMe
Repository name:      spec-tools
Workflow name:        publish.yml
Environment name:     pypi
```

5. Click **Add**

**Important:** The project name must be exactly `spec-tools`. PyPI will reserve this name for you until the first publish.

### 1.3 What This Does

This tells PyPI:
- Trust releases from the `TradeMe/spec-tools` repository
- Only when the `publish.yml` workflow runs
- Only when using the `pypi` GitHub environment
- No API tokens needed - uses OIDC for secure authentication

## Step 2: Set Up TestPyPI Trusted Publishing

### 2.1 Create TestPyPI Account

TestPyPI is separate from PyPI:
1. Go to https://test.pypi.org/account/register/
2. Create your account (can use same email as PyPI)
3. Verify your email

### 2.2 Configure Trusted Publisher for TestPyPI

1. Go to https://test.pypi.org and log in
2. Click your username → **Account settings**
3. Scroll to **Publishing** section
4. Click **Add a new pending publisher**

Fill in these details:
```
PyPI Project Name:    spec-tools
Owner:                TradeMe
Repository name:      spec-tools
Workflow name:        publish.yml
Environment name:     testpypi
```

5. Click **Add**

### 2.3 What This Does

TestPyPI is used for:
- Automatic dev versions (every merge to main)
- Testing releases before publishing to PyPI
- Verifying the package builds correctly

## Step 3: Configure GitHub Environments

### 3.1 Create the `pypi` Environment

1. Go to your GitHub repository
2. Click **Settings** → **Environments**
3. Click **New environment**
4. Name: `pypi`
5. Click **Configure environment**

**Optional but recommended protection rules:**

- ✅ **Required reviewers**: Add yourself or team members
  - This adds a manual approval step before publishing to PyPI
  - Good for production safety

- ✅ **Deployment branches**: Select "Selected branches"
  - Add pattern: `main`
  - Prevents accidental releases from feature branches

6. Click **Save protection rules**

### 3.2 Create the `testpypi` Environment

1. Still in Settings → Environments
2. Click **New environment**
3. Name: `testpypi`
4. Click **Configure environment**

**No protection rules needed** - this is for automatic testing

5. Click **Save protection rules** (or just leave it empty)

### 3.3 What This Does

Environments provide:
- Deployment protection (manual approval for PyPI)
- Audit trail of all releases
- Separate OIDC authentication contexts
- Ability to add secrets if needed later

## Step 4: Create GitHub Label

### 4.1 Create the `release` Label

1. Go to your repository → **Issues**
2. Click **Labels**
3. Click **New label**

Fill in:
```
Label name:        release
Description:       Marks PRs that are allowed to change the version
Color:             #7057ff (or any color you prefer)
```

4. Click **Create label**

### 4.2 What This Does

The `release` label:
- Allows release PRs to bypass version-check workflow
- Triggers automatic release creation on merge
- Visual indicator that a PR is a release

## Step 5: Verify Setup

### 5.1 Check PyPI Configuration

1. Go to https://pypi.org → Your account → Publishing
2. You should see `spec-tools` in "Pending publishers"
3. Status should show waiting for first publish

### 5.2 Check TestPyPI Configuration

1. Go to https://test.pypi.org → Your account → Publishing
2. You should see `spec-tools` in "Pending publishers"
3. Status should show waiting for first publish

### 5.3 Check GitHub Environments

1. GitHub repo → Settings → Environments
2. You should see two environments:
   - `pypi` (with protection rules)
   - `testpypi` (no protection rules)

### 5.4 Check GitHub Label

1. GitHub repo → Issues → Labels
2. You should see `release` label

## Step 6: Test the Setup

### 6.1 Test with a Dev Version (Automatic)

The easiest test is to merge any PR to `main`:

1. Create a small PR (e.g., fix a typo in README)
2. Merge it to `main`
3. Watch the "Publish" workflow run in Actions
4. It should publish a dev version to TestPyPI
5. Check https://test.pypi.org/project/spec-tools/

If successful, you'll see a version like `0.1.0.dev123+abc1234`

### 6.2 Test with a Release (When Ready)

When you're ready for your first release:

1. In a Claude Code session, say: "Make a release for version 0.1.0"
2. Review and merge the PR Claude creates
3. Watch for:
   - "Create Release" workflow creates GitHub release
   - "Publish" workflow publishes to PyPI
4. Check https://pypi.org/project/spec-tools/

If successful, your package is live!

## Troubleshooting

### "Trusted publisher not found" Error

**Problem:** Workflow fails with trusted publisher error

**Solution:**
1. Verify the PyPI trusted publisher configuration exactly matches:
   - Repository: `TradeMe/spec-tools`
   - Workflow: `publish.yml`
   - Environment: `pypi` (or `testpypi`)
2. Check there are no typos
3. Make sure you're using the right PyPI account

### "Project name already taken" on PyPI

**Problem:** Someone else registered `spec-tools` on PyPI

**Solutions:**
1. Choose a different name (e.g., `trademe-spec-tools`)
2. Update everywhere:
   - `pyproject.toml` name field
   - PyPI trusted publisher configuration
   - All documentation references

### GitHub Environment Not Found

**Problem:** Workflow fails saying environment doesn't exist

**Solution:**
1. Check Settings → Environments
2. Name must match exactly: `pypi` or `testpypi` (lowercase)
3. Re-run the workflow after creating the environment

### "release" Label Not Applied

**Problem:** Version check fails on release PR

**Solution:**
1. Manually add the `release` label to the PR
2. The label must be named exactly `release` (lowercase)
3. For Claude-created PRs, this should be automatic

### Permission Denied on Workflow

**Problem:** Workflow fails with permission error

**Solution:**
1. Check Settings → Actions → General
2. Under "Workflow permissions", select:
   - "Read and write permissions"
3. Or add explicit permissions to the workflow file (already done)

## Security Notes

### Why Trusted Publishing is Secure

Traditional PyPI publishing requires API tokens:
- ❌ Tokens can be leaked in logs
- ❌ Tokens can be stolen from environment variables
- ❌ Tokens never expire unless manually rotated
- ❌ Tokens have broad permissions

Trusted Publishing (OIDC):
- ✅ No secrets stored in GitHub
- ✅ No long-lived credentials
- ✅ Short-lived tokens generated per-workflow
- ✅ Scoped to specific repository/workflow/environment
- ✅ Automatic rotation with every use

### Best Practices

1. **Enable environment protection** for `pypi`
   - Requires manual approval before publishing
   - Prevents accidental releases

2. **Review the release PR carefully**
   - Check version number
   - Review CHANGELOG.md changes
   - Verify CI passes

3. **Monitor PyPI downloads**
   - Check for unusual activity
   - Set up PyPI notifications

4. **Keep main branch protected**
   - Require PR reviews
   - Require status checks to pass

## What Happens After Setup

Once everything is configured:

1. **Every PR merged to main:**
   - Dev version published to TestPyPI automatically
   - Can test immediately with:
     ```bash
     pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ spec-tools
     ```

2. **When you say "make a release":**
   - Claude creates release PR
   - You merge the PR
   - GitHub release created automatically
   - Package published to PyPI automatically
   - Available via: `pip install spec-tools`

## Summary Checklist

Before your first release, verify:

- [ ] PyPI account created
- [ ] PyPI trusted publisher configured for `spec-tools`
- [ ] TestPyPI account created
- [ ] TestPyPI trusted publisher configured for `spec-tools`
- [ ] GitHub `pypi` environment created (with protection)
- [ ] GitHub `testpypi` environment created
- [ ] GitHub `release` label created
- [ ] First test: merge a PR and check TestPyPI

That's it! You're ready to publish to PyPI.

## Getting Help

If you run into issues:

1. **Check workflow logs**: Actions tab → Failed workflow → View logs
2. **Check PyPI setup**: PyPI account → Publishing → Verify configuration
3. **Check GitHub setup**: Settings → Environments and Labels
4. **Common issues**: See Troubleshooting section above

For PyPI-specific issues:
- PyPI Help: https://pypi.org/help/
- Trusted Publishing Docs: https://docs.pypi.org/trusted-publishers/
