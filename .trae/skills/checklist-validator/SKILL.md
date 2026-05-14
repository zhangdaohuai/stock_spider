---
name: "checklist-validator"
description: "Validates checklists against deliverables and generates review-signed commits to lock state. Invoke when user needs to verify acceptance criteria, validate a checklist before commit, or lock a reviewed state with a signed commit."
---

# Checklist Validator

Validates deliverables against checklists and generates review-signed commits to lock verified state. Ensures every committed change has passed a structured validation gate.

## When to Invoke

- User asks to validate a checklist or acceptance criteria
- User wants to commit changes with review verification
- User mentions "lock state", "review sign", "checklist pass", or "validation gate"
- Before committing feature work that has associated acceptance criteria
- User asks to verify that all items in a checklist are addressed

## Core Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ 1. Load Checklist │────▶│ 2. Validate Items │────▶│ 3. Generate Report │────▶│ 4. Signed Commit  │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
```

### Phase 1: Load Checklist

Identify the checklist source:

| Source | How to Load |
|--------|------------|
| Acceptance Criteria in PRD/Issue | Read the document, extract `## Acceptance Criteria` or `AC-xxx` items |
| `deliver-acceptance-criteria` output | Read the generated acceptance criteria file |
| `deliver-launch-checklist` output | Read the launch checklist file |
| User-provided checklist | Parse the user's explicit list |
| Inline checklist in code comments | Scan for `// CHECKLIST:` or `<!-- CHECKLIST: -->` markers |

### Phase 2: Validate Items

For each checklist item, verify:

| Check | Method | Pass Criteria |
|-------|--------|--------------|
| **Code exists** | Search codebase for relevant files/functions | Implementation found |
| **Tests exist** | Search for test files covering the item | Test file found with matching test name |
| **Tests pass** | Run the test suite | All related tests pass |
| **Lint clean** | Run linter on changed files | No errors (warnings acceptable) |
| **Type check** | Run type checker if available | No type errors |
| **Documentation** | Check for updated docs/comments | Doc strings or README updated |

**Validation Result per Item**:

| Status | Meaning |
|--------|---------|
| ✅ PASS | All checks passed |
| ⚠️ PARTIAL | Some checks passed, others skipped or inconclusive |
| ❌ FAIL | One or more critical checks failed |
| ⏭️ SKIP | Item not applicable or explicitly deferred |

### Phase 3: Generate Validation Report

Output a structured validation report:

```markdown
## Checklist Validation Report

**Date**: YYYY-MM-DDTHH:MM:SSZ
**Scope**: [feature/module description]
**Checklist Source**: [where the checklist came from]

### Validation Summary

| Status | Count |
|--------|-------|
| ✅ PASS | N |
| ⚠️ PARTIAL | N |
| ❌ FAIL | N |
| ⏭️ SKIP | N |

**Overall**: PASS / PARTIAL / FAIL

### Item Details

| ID | Item | Status | Evidence |
|----|------|--------|----------|
| AC-001 | [description] | ✅ PASS | [file:line] test passed |
| AC-002 | [description] | ⚠️ PARTIAL | code exists, no test |
| AC-003 | [description] | ❌ FAIL | missing implementation |

### Failed Items Detail

#### AC-003: [description]
- **Expected**: [what should be true]
- **Actual**: [what was found]
- **Action Required**: [what needs to be done]

### Gate Decision

- [ ] **PASS** → Proceed to signed commit
- [ ] **PARTIAL** → Proceed with warnings (requires user confirmation)
- [ ] **FAIL** → Block commit, fix failed items first
```

### Phase 4: Signed Commit

When validation passes (PASS or PARTIAL with user confirmation), generate a review-signed commit.

**Commit Format**:

```
<type>[scope]: <description>

Validated-by: Checklist-Validator
Checklist: <source>
Pass: N/N items
Status: PASS | PARTIAL

Checklist-Items:
- [x] AC-001: <description>
- [x] AC-002: <description>
- [~] AC-003: <description> (PARTIAL)
- [ ] AC-004: <description> (SKIP)

Review-Signature: <hash>
State: LOCKED
```

**Review Signature Generation**:

The review signature is a deterministic hash of:
1. Commit SHA (after commit is created)
2. Checklist source identifier
3. Pass/fail status of each item
4. Timestamp

```bash
# Generate review signature
echo "<commit-sha>:<checklist-source>:<item-statuses>:<timestamp>" | shasum -a 256 | cut -d' ' -f1
```

**Amending Commit with Signature**:

```bash
# After initial commit, amend with the signature
git commit --amend --no-edit
```

## State Locking Rules

| Rule | Description |
|------|-------------|
| **LOCKED** | All items PASS → commit is locked, no further changes to this scope |
| **LOCKED-WARN** | Some items PARTIAL → locked with warnings, partial items tracked |
| **UNLOCKED** | Any item FAIL → commit blocked, must fix before locking |

**Lock Enforcement**:

- After a LOCKED commit, any subsequent change to the same scope requires a new checklist validation
- LOCKED state is indicated by the `State: LOCKED` footer in the commit message
- Use `git log --grep="State: LOCKED"` to find locked commits
- Use `git log --grep="Review-Signature:"` to find review-signed commits

## Integration with Other Skills

| Skill | Integration Point |
|-------|------------------|
| `deliver-acceptance-criteria` | Use its output as the checklist source |
| `deliver-launch-checklist` | Validate launch readiness before commit |
| `deliver-edge-cases` | Include edge case coverage in validation |
| `git-commit` | Use signed commit format instead of plain conventional commit |
| `bug-fixer` | Validate bug fix against root cause checklist |
| `incident-commander` | Validate incident response against SEV checklist |

## Quick Reference

### Validate and Commit (Full Flow)

```
1. Load checklist from source
2. Validate each item against codebase
3. Generate validation report
4. If PASS → create signed commit with State: LOCKED
5. If PARTIAL → ask user, then create signed commit with State: LOCKED-WARN
6. If FAIL → report failures, block commit
```

### Validate Only (No Commit)

```
1. Load checklist from source
2. Validate each item against codebase
3. Generate validation report
4. Return report to user
```

### Verify Existing Locked State

```
1. Find locked commits: git log --grep="State: LOCKED"
2. Verify signature: check Review-Signature matches expected hash
3. Report lock status and integrity
```

## Safety Rules

1. **Never auto-commit on FAIL** — Block commit if any item fails validation
2. **Never skip user confirmation on PARTIAL** — Always ask before proceeding
3. **Never modify a locked commit** — Create a new commit instead of amending a LOCKED one
4. **Never forge review signatures** — Signatures must be deterministically generated
5. **Always include checklist source** — Traceability requires knowing where the checklist came from
6. **Always run tests before PASS** — A checklist item is not PASS unless tests exist and pass
