> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Advanced Diagram Types

Less-common but powerful Mermaid diagram types. Each section covers the declaration keyword, core syntax constructs, and one working example.

SOURCE: [Mermaid.js Official Documentation](https://mermaid.js.org) (accessed 2026-03-07) — Mermaid v11.12.3+

---

## Block Diagram

**Declaration**: `block-beta`

**Core constructs:**

- `columns N` — set grid width
- `BlockID["Label"]` — named block (rectangle default)
- `BlockID[N]` — block spanning N columns
- `space` / `space:N` — empty cell(s)
- Nested composite: `Outer[ Inner1 Inner2 ]`
- Edges: `A --> B`, `A --> |label| B`, `A --- B`, `A -. B`
- Shapes: `(rounded)`, `([stadium])`, `((circle))`, `{rhombus}`, `[(cylinder)]`
- Styling: `style A fill:#f9f`, `classDef name fill:#0f0`

```mermaid
block-beta
    columns 3

    Input["Data Input"]
    Process["Process Data"]
    Output["Output Results"]

    space

    Input --> Process --> Output

    style Input fill:#E3F2FD
    style Process fill:#F3E5F5
    style Output fill:#E8F5E9
```

---

## Sankey Diagram

**Declaration**: `sankey-beta`

**Core constructs:**

- CSV format — three columns: `source,target,value`
- First row is data (no header row)
- Values must be positive numbers
- Wrap values containing commas in quotes
- `linkColor`: `source` | `target` | `gradient` | hex
- `nodeAlignment`: `justify` | `center` | `left` | `right`

```mermaid
sankey-beta
Salary,Housing,2000
Salary,Food,800
Salary,Transportation,300
Salary,Savings,500
Bonus,Travel,1000
Bonus,Investment,1500
```

---

## C4 Diagram

**Declaration**: `C4Context` | `C4Container` | `C4Component` | `C4Dynamic` | `C4Deployment`

**Status**: Experimental — syntax may change

**Diagram types:**

| Keyword | View |
|---------|------|
| `C4Context` | System context — people and systems |
| `C4Container` | Container breakdown within a system |
| `C4Component` | Component details within a container |
| `C4Dynamic` | Interaction sequences |
| `C4Deployment` | Infrastructure deployment |

**Core constructs:**

- `Person(id, "Label", "Description")` — human actor
- `System(id, "Label", "Description")` — internal system
- `System_Ext(id, "Label", "Description")` — external system
- `Container(id, "Label", "Tech", "Description")` — container
- `Rel(from, to, "Label")` — relationship
- `UpdateElementStyle("id", color, text_color)` — override element style
- `UpdateRelStyle(from, to, color, text)` — override relationship style

```mermaid
C4Context
    title E-Commerce Platform Context

    Person(customer, "Customer", "User purchasing products")
    System(ecommerce, "E-Commerce Platform", "Online shopping system")
    System_Ext(payment, "Payment Gateway", "Processes transactions")
    System_Ext(email, "Email Service", "Sends notifications")

    Rel(customer, ecommerce, "Uses")
    Rel(ecommerce, payment, "Processes payments")
    Rel(ecommerce, email, "Sends emails via")
```

---

## Architecture Diagram

**Declaration**: `architecture-beta`

**Introduced**: v11.1.0+

**Core constructs:**

- `service id(icon)[Label]` — service node; built-in icons: `cloud`, `database`, `disk`, `internet`, `server`
- `group id(icon)[Label]` — named group containing services
- `junction id` — connection point for branching edges
- Edge syntax: `serviceA:SIDE --> SIDE:serviceB` where SIDE is `T` | `R` | `B` | `L`
- Arrow types: `-->` (right), `<--` (left), `<-->` (bidirectional), `--` (none)
- Extended icons via `name:icon-name` format (iconify.design)

```mermaid
architecture-beta
    group api_layer(cloud)[API Layer]
        service api_gateway(server)[API Gateway]
        service auth_service(server)[Auth Service]

    group data_layer(database)[Data Layer]
        service primary_db(database)[Primary DB]
        service cache(disk)[Redis Cache]

    api_gateway:B --> T:primary_db
    api_gateway:R --> L:cache
    auth_service --> primary_db
```

---

## Kanban Diagram

**Declaration**: `kanban`

**Introduced**: v11.1.0+

**Core constructs:**

- `columnId[Column Title]` — board column
- `taskId[Task Description]` — item within a column (indented under column)
- Task metadata block: `taskId[Name]@{ assigned: "User", ticket: "ID", priority: "Level" }`
- Priority values: `Very High` | `High` | `Medium` | `Low` | `Very Low`
- Config option: `ticketBaseUrl` — template URL for ticket links (use `#TICKET#` placeholder)

```mermaid
kanban
    ToDo[To Do]
        task1[Design API endpoints]@{
            assigned: Alice
            ticket: API-001
            priority: Very High
        }

    InProgress[In Progress]
        task2[Implement auth]@{
            assigned: Bob
            ticket: AUTH-001
            priority: Very High
        }

    Done[Completed]
        task3[Setup CI/CD]@{
            assigned: Charlie
            ticket: DEVOPS-001
        }
```

---

## Packet Diagram

**Declaration**: `packet-beta`

**Core constructs:**

- Absolute range syntax: `0-7: "Field Name"` — field spans bit positions 0 through 7
- Relative bits syntax (v11.7.0+): `+N: "Field Name"` — field occupies N bits from current position
- Config options: `bitsperrow` (default 32), `bitwidth`, `rowheight`, `showbits`

```mermaid
packet-beta
    +1: "SYN"
    +1: "ACK"
    +6: "Reserved"
    +16: "Window Size"
    +32: "Sequence Number"
    +32: "Acknowledgment"
    +16: "Checksum"
    +16: "Urgent Pointer"
```

---

## Requirement Diagram

**Declaration**: `requirementDiagram`

**Core constructs:**

- Requirement block types: `requirement`, `functionalRequirement`, `interfaceRequirement`, `performanceRequirement`, `physicalRequirement`, `designConstraint`
- Requirement fields: `id`, `text`, `risk` (`Low` | `Medium` | `High`), `verifymethod` (`Analysis` | `Inspection` | `Test` | `Demonstration`)
- Element block: `element id { type: T, docref: path }` — implementation artifact
- Relationship: `reqA - <type> -> reqB` where type is `contains` | `copies` | `derives` | `satisfies` | `verifies` | `refines` | `traces`

```mermaid
requirementDiagram
    requirement authentication {
        id: AUTH-001
        text: System shall support user authentication
        risk: High
        verifymethod: Test
    }

    requirement password_strength {
        id: AUTH-002
        text: Passwords must be at least 8 characters
        risk: Medium
        verifymethod: Analysis
    }

    element login_service {
        type: Software
        docref: docs/auth-service
    }

    authentication - contains -> password_strength
    authentication - satisfies -> login_service
```

---

## Radar Chart

**Declaration**: `radar-beta`

**Introduced**: v11.6.0+

**Core constructs:**

- `axis A, B, C, ...` — define axis labels (comma-separated)
- `curve "Name" {v1, v2, v3, ...}` — one data series; values correspond to axes in order
- Config options: `showLegend`, `max`, `min`, `graticule` (`circle` | `polygon`), `ticks`

```mermaid
radar-beta
    title Tech Skills Assessment

    axis JavaScript, TypeScript, React, Node.js, Python

    curve Alice {4, 5, 5, 4, 3}
    curve Bob {3, 2, 3, 5, 4}
```

---

## Treemap Diagram

**Declaration**: `treemap-beta`

**Introduced**: v11.6.0+

**Core constructs:**

- `"Parent Section"` — container node (no value; quoted)
- `"Leaf Node" : N` — leaf node with numeric value
- Indentation defines hierarchy depth
- Config options: `showValues`, `valueFormat` (D3 number format specifier), `padding`, `useMaxWidth`

```mermaid
treemap-beta
    "Annual Expenses"
        "Operations" : 250000
            "Rent" : 100000
            "Utilities" : 50000
            "Maintenance" : 100000
        "Personnel" : 500000
            "Engineering" : 300000
            "Support" : 50000
        "Marketing" : 150000
```

---

## Venn Diagram

**Declaration**: `venn-beta`

**Introduced**: v11.12.3+

**Core constructs:**

- `set A["Label"]` — define a named set
- `set A: N` — optional size modifier
- `text A: "Content"` — text inside a set region
- `text AB: "Content"` — text inside the intersection of sets A and B
- `text ABC: "Content"` — text inside triple intersection
- Intersection IDs are formed by concatenating set IDs in declaration order (no separator)

```mermaid
venn-beta
    title Programming Language Skills

    set Python["Python"]
    set JavaScript["JavaScript"]
    set Go["Go"]

    text Python: "Data Science<br/>ML"
    text JavaScript: "Web<br/>Frontend"
    text Go: "DevOps<br/>Performance"

    text PythonJavaScript: "Scripting<br/>Backends"
    text PythonGo: "Automation"
    text PythonJavaScriptGo: "Full Stack"
```

---

## ZenUML Diagram

**Declaration**: `zenuml`

**Core constructs:**

- Participants: `actor Name`, `participant Name as Alias`
- Synchronous message: `A -> B: Label` (blocking)
- Asynchronous message: `A => B: Label` (fire-and-forget)
- Reply: `A <- B: Label`
- Object creation: `new ClassName: label`
- Control flow: `loop "condition" { }`, `if "cond" { } else { }`, `opt "label" { }`, `par { } par { } end`, `try { } catch { } finally { }`
- Comments: `// text` (supports `**bold**` and `*italic*`)

```mermaid
zenuml
    actor User
    participant Client as Web Client
    participant Server as API Server
    participant DB as Database

    User -> Client: Click button
    Client => Server: POST /api/data

    par
        Server -> DB: Save data
    par
        Server -> Server: Process
    end

    Server <- DB: Confirm
    Client <- Server: Success
    User <- Client: Show result
```

---

## See Also

- [Flowchart Syntax](../SKILL.md)
- [Data Charts](./data-charts.md)
- [Mindmap](./mindmap.md)
