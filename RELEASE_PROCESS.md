# Release Process for Claude Code

This document provides step-by-step instructions for Claude Code to prepare a release PR when the user requests "make a release" or similar.

## Overview

**User's role:** Request a release and provide the version number, then merge the PR

**Claude's role:** Everything else - update files, create PR, label it

**Automation's role:** On PR merge, automatically create GitHub release and publish to PyPI

## When User Says "Make a Release"

Follow these steps exactly:

### Step 1: Confirm Version Number

Ask the user what version to release if not specified:
- Follow semantic versioning: MAJOR.MINOR.PATCH
- For pre-releases: MAJOR.MINOR.PATCH-alpha.N, -beta.N, or -rc.N
- Examples: `0.2.0`, `1.0.0-alpha.1`, `0.2.1`

### Step 2: Validate Prerequisites

Check that:
1. We're on the correct branch (usually `main` or the development branch)
2. All tests pass: `uv run pytest tests/ -v`
3. All linters pass: `uv run ruff check && uv run ruff format --check`
4. CHANGELOG.md has content in the `[Unreleased]` section

If any checks fail, inform the user and ask if they want to proceed anyway.

### Step 3: Update Version in pyproject.toml

```bash
# Update the version line
sed -i 's/^version = .*/version = "VERSION_HERE"/' pyproject.toml
```

Replace `VERSION_HERE` with the target version (e.g., `0.2.0`).

### Step 4: Update CHANGELOG.md

This is the most important step for release notes!

1. Read the current CHANGELOG.md
2. Get today's date in format YYYY-MM-DD
3. Find the `## [Unreleased]` section
4. Move its content to a new version section: `## [VERSION] - DATE`
5. Leave `## [Unreleased]` section empty for future changes
6. Update the comparison links at the bottom

**Example transformation:**

Before:
```markdown
## [Unreleased]

### Added
- New feature X

### Fixed
- Bug Y

## [0.1.0] - 2025-01-15
...

[Unreleased]: https://github.com/TradeMe/spec-tools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/TradeMe/spec-tools/releases/tag/v0.1.0
```

After (for version 0.2.0 on 2025-10-26):
```markdown
## [Unreleased]

## [0.2.0] - 2025-10-26

### Added
- New feature X

### Fixed
- Bug Y

## [0.1.0] - 2025-01-15
...

[Unreleased]: https://github.com/TradeMe/spec-tools/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/TradeMe/spec-tools/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/TradeMe/spec-tools/releases/tag/v0.1.0
```

**Critical:** The content under the version header becomes the GitHub release notes!

### Step 5: Create Release Branch and Commit

```bash
# Create release branch
git checkout -b release/vVERSION

# Stage changes
git add pyproject.toml CHANGELOG.md

# Commit with standard message
git commit -m "chore: Prepare release vVERSION

- Update version to VERSION in pyproject.toml
- Update CHANGELOG.md with release date

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push branch
git push -u origin release/vVERSION
```

### Step 6: Create Pull Request

Use the `gh` CLI or GitHub API to create the PR:

```bash
gh pr create \
  --title "Release vVERSION" \
  --body "# Release vVERSION

This PR prepares the release of version VERSION.

## Changes

See [CHANGELOG.md](./CHANGELOG.md) for details.

## Checklist

- [x] Version updated in \`pyproject.toml\`
- [x] \`CHANGELOG.md\` updated with release date
- [x] All tests passing (verified by CI)

## What Happens on Merge

1. **Automatic GitHub Release**: A release will be created with tag \`vVERSION\`
2. **Release Notes**: Extracted automatically from CHANGELOG.md
3. **PyPI Publishing**: Package will be published to PyPI
4. **TestPyPI**: A dev version was already published for testing

## Installation After Release

\`\`\`bash
pip install --upgrade spec-tools
\`\`\`

🤖 Generated with [Claude Code](https://claude.com/claude-code)" \
  --label "release" \
  --base main
```

**Important:** The PR MUST have the `release` label! This:
- Allows it to bypass the version-check workflow
- Triggers automatic release creation on merge

### Step 7: Inform the User

Tell the user:

```
✅ Release PR created: [link to PR]

**Next steps:**
1. Review the PR (especially CHANGELOG.md)
2. Wait for CI to pass
3. Merge the PR

**What happens automatically after merge:**
- GitHub release created with tag vVERSION
- Release notes extracted from CHANGELOG.md
- Package published to PyPI
- PR commented with release link

You can then install with: `pip install --upgrade spec-tools`
```

## Common Scenarios

### Pre-release (Alpha/Beta/RC)

Same process, just use version like `0.2.0-alpha.1`. The automation will:
- Mark the GitHub release as "pre-release"
- Still publish to PyPI (users can opt-in with `pip install spec-tools==0.2.0-alpha.1`)

### Patch Release

Same process with version like `0.1.1`. Make sure CHANGELOG.md has the fixes documented.

### Emergency Hotfix

If CI is broken or there's urgency:
1. Still create the release PR (don't skip process)
2. User can merge even with failing CI (their decision)
3. Fix issues in follow-up PR

## Troubleshooting

### "CHANGELOG.md has no unreleased content"

- Check if there are changes to document
- If not, ask user if they still want to release (maybe just dependency updates)
- Can add a minimal entry: "### Changed\n- Dependency updates"

### "Version already exists"

- Check git tags: `git tag | grep vVERSION`
- If tag exists, need to bump to next version
- Ask user for a different version number

### "CI failing"

- Fix the issues first if possible
- If urgent, inform user they can merge anyway (their call)

### "PR creation failed"

- Check if branch already exists
- Try fetching latest: `git fetch origin`
- May need to use a different branch name

## Testing the Release Process

Before merging a release PR, you can verify:

1. **Check the diff:** Does it only change version and CHANGELOG?
2. **Verify CHANGELOG format:** Is the version section properly formatted?
3. **Check CI:** Are all checks passing?
4. **Review release notes:** Will the CHANGELOG section make good release notes?

## After Release

After the user merges and the release is published, you can:

1. Verify the release was created: Check GitHub releases
2. Verify PyPI publishing: Check Actions > Publish workflow
3. Test installation: `pip install --upgrade spec-tools==VERSION`

The user might ask you to verify - if so, check the GitHub releases page and workflow runs.
