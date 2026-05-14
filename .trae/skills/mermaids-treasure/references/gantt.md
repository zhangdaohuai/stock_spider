> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Gantt Chart

**Declaration**: `gantt`

SOURCE: Official Mermaid.js documentation (<https://mermaid.js.org/syntax/gantt.html>) (accessed 2026-03-07)

---

## Minimal Structure

```mermaid
gantt
    title My Project
    dateFormat YYYY-MM-DD

    section Phase 1
    Task A :a1, 2024-01-01, 5d
    Task B :after a1, 3d
```

---

## Configuration Directives

Place these at the top of the chart, before any sections:

```mermaid
gantt
    title         Project Title
    dateFormat    YYYY-MM-DD
    axisFormat    %b %d
    tickInterval  1week
    todayMarker   on
    excludes      weekends
    includes      2024-01-01,2024-12-25
```

| Directive     | Purpose                                              | Example value          |
|---------------|------------------------------------------------------|------------------------|
| `title`       | Chart heading                                        | `Sprint 4`             |
| `dateFormat`  | Input date parsing format                            | `YYYY-MM-DD`           |
| `axisFormat`  | Axis label display format (strftime tokens)          | `%m/%d`                |
| `tickInterval` | Axis tick spacing                                   | `1day`, `1week`, `1month` |
| `todayMarker` | Show/hide the "today" vertical line                  | `on` (default) / `off` |
| `excludes`    | Dates or keywords to skip (tasks stretch around them) | `weekends`, `2024-01-01` |
| `includes`    | Override excludes — force specific dates back in     | `2024-12-26`           |

---

## Sections and Tasks

```mermaid
gantt
    title Feature Rollout
    dateFormat YYYY-MM-DD

    section Backend
    API design     :done,  api,  2024-01-01, 5d
    Implementation :crit,  impl, after api,  10d

    section Frontend
    UI mockups     :active, ui,  2024-01-03, 7d
    Integration    :        int, after impl, 5d
```

Task syntax:

```text
<label> :<status>, <id>, <start>, <duration>
<label> :<status>, <id>, after <otherId>, <duration>
```

All fields after the first `:` are optional and order-insensitive within a slot — but the common convention is `status, id, start/after, duration`.

---

## Task Status Tags

```text
active      Currently in progress — highlighted in blue
done        Completed — greyed out
crit        Critical path — highlighted in red
milestone   Zero-duration marker — diamond shape (use 0d duration)
```

Tags combine:

```mermaid
gantt
    dateFormat YYYY-MM-DD

    section Milestones
    Sprint complete :crit, milestone, m1, 2024-02-01, 0d
    Deploy to prod  :crit, active,    d1, 2024-02-01, 2d
    Hotfix done     :done, crit,      h1, 2024-01-28, 1d
```

---

## Task Dependencies

Use `after <id>` to chain tasks. Multiple dependencies use `after <id1> <id2>`:

```mermaid
gantt
    dateFormat YYYY-MM-DD

    section Build
    Design   :des, 2024-01-01, 5d
    Backend  :be,  after des,  8d
    Frontend :fe,  after des,  6d
    QA       :qa,  after be fe, 4d
```

`after be fe` means QA starts only after both Backend and Frontend complete.

---

## Date Formats

**Input date tokens** (used in `dateFormat`):

| Token | Meaning        |
|-------|----------------|
| `YYYY` | 4-digit year  |
| `MM`   | 2-digit month |
| `DD`   | 2-digit day   |

**Axis display tokens** (used in `axisFormat`, strftime-style):

| Token | Output          |
|-------|-----------------|
| `%Y`  | 4-digit year    |
| `%m`  | 2-digit month   |
| `%d`  | 2-digit day     |
| `%b`  | Abbreviated month name (Jan, Feb…) |
| `%j`  | Day of year     |

**Duration units**: `d` (days), `w` (weeks), `h` (hours), `m` (minutes), `s` (seconds).

---

## v11+ Features

Mermaid v11 (v11.12.3+ as of 2026-03-07) did not introduce Gantt-specific new syntax; however, the global `%%{init: {...}}%%` front-matter configuration applies to Gantt charts and enables theme and config overrides at render time:

```mermaid
%%{init: {"theme": "dark", "gantt": {"barHeight": 20, "fontSize": 14}}}%%
gantt
    title Dark-themed Gantt
    dateFormat YYYY-MM-DD

    section Work
    Task :a1, 2024-01-01, 5d
```

Supported `gantt` config keys via `%%{init}%%`:

```text
barHeight           Height of each task bar in pixels
barGap              Gap between bars
topPadding          Space above first bar
rightPadding        Right margin
leftPadding         Left margin
gridLineStartPadding  Grid line offset
fontSize            Text size
fontFamily          Font face
numberSectionStyles Number of alternating section color styles (1-4)
axisFormat          Overrides directive-level axisFormat
```

---

## Complete Example

```mermaid
gantt
    title Product Development Roadmap
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    tickInterval 1week
    excludes weekends

    section Planning
    Requirements       :req,    2024-01-01, 7d
    Design             :design, after req,  10d

    section Development
    Backend            :crit, dev1, after design, 14d
    Frontend           :dev2, after design,        12d
    Integration        :crit, dev3, after dev1,     5d
    Testing            :test, after dev3,            7d

    section Deployment
    Staging Deploy     :deploy1, after test,    2d
    Production Release :crit, milestone, m1, after deploy1, 0d
    Post-Launch Support :support, after m1,   10d
```

---

## See Also

- [Flowchart Syntax](../SKILL.md)
- [Timeline & Journey](./timeline-journey.md)
