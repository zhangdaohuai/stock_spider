> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Git Graph

Visualizes Git branching history — commits, branches, merges, and cherry-picks.

## Declaration

```mermaid
gitGraph LR:
    commit
```

Orientation is specified on the declaration line. Supported values:

- `LR` — left-to-right (default)
- `TB` — top-to-bottom
- `BT` — bottom-to-top

## Commands

### commit

Creates a commit on the current branch.

```mermaid
gitGraph LR:
    commit
    commit id: "named-commit"
    commit id: "tagged" tag: "v1.0.0"
    commit type: HIGHLIGHT
```

Options:

| Option | Values | Effect |
|--------|--------|--------|
| `id` | string | Sets commit label |
| `tag` | string | Attaches version tag |
| `type` | `NORMAL`, `REVERSE`, `HIGHLIGHT` | Changes commit marker shape |

Commit type markers:

- `NORMAL` — open circle (default)
- `REVERSE` — crossed circle
- `HIGHLIGHT` — filled rectangle

### branch

Creates a new branch at the current HEAD position.

```mermaid
gitGraph LR:
    commit
    branch feature/login
    commit id: "Add login form"
```

### checkout

Switches the active branch. Subsequent `commit` calls land on this branch.

```mermaid
gitGraph LR:
    commit
    branch develop
    commit id: "Work on develop"
    checkout main
    commit id: "Back on main"
```

### merge

Merges a named branch into the current branch.

```mermaid
gitGraph LR:
    commit
    branch feature
    commit id: "Feature work"
    checkout main
    merge feature tag: "v1.1.0"
```

### cherry-pick

Applies a specific commit (by id) onto the current branch.

```mermaid
gitGraph LR:
    commit id: "base"
    branch hotfix
    commit id: "critical-fix"
    checkout main
    cherry-pick id: "critical-fix"
```

## Branch Ordering

Branches render in the order they are declared. Use `mainBranchOrder` to control position of the main branch among others.

## Direction

```mermaid
gitGraph TB:
    commit id: "Initial"
    branch feature
    commit id: "Feature work"
    checkout main
    merge feature
```

`TB` is useful when branch names are long or when embedding in narrow layouts.

## Theme Variables for Colors

Branch colors cycle through theme variables. Override in a `%%{init}%%` block:

```mermaid
%%{init: { 'logLevel': 'debug', 'theme': 'default', 'themeVariables': { 'git0': '#ff0000', 'git1': '#00ff00', 'git2': '#0000ff' } } }%%
gitGraph LR:
    commit
    branch feature
    commit
    checkout main
    merge feature
```

Variables `git0` through `git7` map to branch colors in declaration order.

## Configuration Options

Passed via `%%{init}%%` under `'gitGraph'`:

| Option | Default | Effect |
|--------|---------|--------|
| `showBranches` | `true` | Show/hide branch lane labels |
| `showCommitLabel` | `true` | Show/hide commit id text |
| `mainBranchName` | `"main"` | Name of the primary branch |
| `mainBranchOrder` | `0` | Vertical position of main branch |
| `parallelCommits` | `false` | Align concurrent commits on same vertical line |

## v11+ Features

- `BT` orientation support added in v11
- `cherry-pick` command stabilized in v11
- Theme variable override via `%%{init}%%` fully supported in v11

## Complete Example

```mermaid
gitGraph TB:
    commit id: "Initial commit"
    commit id: "Add core features"
    branch feature/auth
    checkout feature/auth
    commit id: "Implement login"
    commit id: "Add password reset"
    checkout main
    branch hotfix/security
    commit id: "Security patch" type: HIGHLIGHT
    checkout main
    merge hotfix/security tag: "v1.0.1"
    checkout feature/auth
    commit id: "Add 2FA"
    checkout main
    merge feature/auth tag: "v1.1.0"
    commit id: "Release notes"
```

## See Also

- [Flowchart Syntax](../SKILL.md)
- [Timeline & Journey](./timeline-journey.md)
