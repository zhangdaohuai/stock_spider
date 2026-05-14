> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Timeline & User Journey

SOURCE: Official Mermaid.js documentation (<https://mermaid.js.org/syntax/timeline.html>, <https://mermaid.js.org/syntax/userJourney.html>) (accessed 2026-03-07)

---

## Timeline

**Declaration**: `timeline`

### Minimal Structure

```mermaid
timeline
    title Project History
    2023 : Initial release
    2024 : Feature expansion : Performance improvements
    2025 : Enterprise launch
```

### Time Periods and Events

Each line is a time period followed by one or more events separated by `:`:

```text
<time-period> : <event1> : <event2> : <event3>
```

Time periods are arbitrary text — dates, quarters, version names, years, or prose labels:

```mermaid
timeline
    title Deployment History
    v1.0 : Authentication : Basic dashboard
    v1.5 : API keys : Webhooks : Rate limiting
    v2.0 : GraphQL : Multi-tenant : Audit log
```

### Section Grouping

Use `section` to group related time periods under a heading:

```mermaid
timeline
    title Product Launch

    section 2024
        January  : Planning starts : Team assembled
        February : Requirements : Architecture design
        March    : Development begins

    section 2025
        January  : Performance pass : Security audit
        March    : Official launch
```

### Multiple Events per Time Period

Append additional `: <event>` segments on the same line:

```mermaid
timeline
    title Sprint Activity
    Sprint 1 : Login page : Password reset : Email verification
    Sprint 2 : Dashboard : Charts
    Sprint 3 : Export to CSV : API docs
```

### Line Breaks in Event Text

Use `<br>` to force a line break inside an event label:

```text
Long feature name : First milestone<br>completed early
```

### Theme and Styling

Apply a theme via `%%{init}%%` front-matter:

```mermaid
%%{init: {"theme": "forest"}}%%
timeline
    title Feature Roadmap
    Q1 : Research : Prototyping
    Q2 : Beta : Feedback collection
    Q3 : GA release
```

Available themes: `default`, `forest`, `dark`, `neutral`, `base`.

### Complete Example

```mermaid
timeline
    title Product Launch Timeline

    section 2024
        January  : Planning starts : Team assembled
        February : Requirements : Architecture design
        March    : Development begins : Backend APIs

    section 2024-2025
        April-May : Frontend development : QA testing
        June      : Beta release : User feedback

    section 2025
        January  : Performance optimization : Security audit
        February : Marketing campaign : Pre-orders begin
        March    : Production deployment : Official launch
```

---

## User Journey

**Declaration**: `journey`

### Minimal Structure

```mermaid
journey
    title User Onboarding
    section Sign Up
        Visit landing page : 5 : User
        Enter email        : 4 : User
        Confirm email      : 3 : User, System
```

### Task Syntax

```text
Task name : <score> : <Actor1>, <Actor2>
```

- **Task name** — free text describing the step
- **score** — satisfaction rating from 1 (low) to 5 (high)
- **Actors** — comma-separated list of participants involved in the step

Scores drive the bar height in the rendered chart. Multiple actors share the same bar.

### Score Range

| Score | Meaning              |
|-------|----------------------|
| 1     | Very unsatisfied     |
| 2     | Unsatisfied          |
| 3     | Neutral              |
| 4     | Satisfied            |
| 5     | Very satisfied       |

### Sections

Group steps into `section` blocks representing journey phases:

```mermaid
journey
    title Checkout Flow
    section Cart
        Add item      : 5 : Customer
        Review cart   : 4 : Customer
    section Payment
        Enter card    : 1 : Customer
        Confirm order : 5 : Customer, System
    section Confirmation
        Email receipt : 5 : Customer, Email
        Track order   : 4 : Customer, System
```

### Complete Example

```mermaid
journey
    title E-Commerce Checkout Journey

    section Discovery
        Browse products     : 4 : Customer
        Search filters      : 5 : Customer, System
        View product details : 4 : Customer, System

    section Cart
        Add to cart      : 5 : Customer
        Review cart      : 4 : Customer
        Update quantities : 3 : Customer

    section Checkout
        Enter shipping   : 2 : Customer
        Select method    : 2 : Customer
        Enter payment    : 1 : Customer, Security
        Confirm order    : 5 : Customer, System

    section Post-Order
        Receive confirmation : 5 : Customer, Email
        Track shipment       : 4 : Customer, System
        Delivery received    : 5 : Customer
```

---

## See Also

- [Flowchart Syntax](../SKILL.md)
- [Gantt](./gantt.md)
- [Git Graph](./git-graph.md)
