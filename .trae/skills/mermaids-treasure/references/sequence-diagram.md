> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Sequence Diagram Syntax

## Declaration

Every sequence diagram begins with `sequenceDiagram` on its own line.

```mermaid
sequenceDiagram
    A ->> B: Hello
```

## Participants and Actors

Declare participants explicitly to control order. Use `actor` for human roles. Aliases shorten long names.

```mermaid
sequenceDiagram
    actor User
    participant Client as Web Client
    participant DB as Database
    User ->> Client: Submit form
    Client ->> DB: Insert record
```

**Participant types** available in v11+: `boundary`, `control`, `entity`, `queue`, `collections` — render with UML stereotype icons.

## Message Types

| Syntax | Line | Arrowhead | Meaning |
|--------|------|-----------|---------|
| `A ->> B: msg` | Solid | Filled | Synchronous call |
| `A -->> B: msg` | Dotted | Filled | Reply / async response |
| `A -> B: msg` | Solid | Open | Solid open arrow |
| `A --> B: msg` | Dotted | Open | Dotted open arrow |
| `A -x B: msg` | Solid | Cross | Destroy / reject |
| `A --x B: msg` | Dotted | Cross | Dotted destroy |
| `A -) B: msg` | Solid | Async | Solid async (fire-and-forget) |
| `A --) B: msg` | Dotted | Async | Dotted async |
| `A ~>> B: msg` | Solid | Async thick | Solid thick async (v11+) |
| `A ~~>> B: msg` | Dotted | Async thick | Dotted thick async (v11+) |

```mermaid
sequenceDiagram
    participant A
    participant B
    A ->> B: Sync call
    B -->> A: Reply
    A -x B: Cancel
    A -) B: Fire and forget
```

## Activation Boxes

Show a participant is active (processing) using `activate`/`deactivate` or the `+`/`-` shorthand on the message line.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    Client ->>+ Server: Request
    Server ->>+ DB: Query
    DB -->>- Server: Rows
    Server -->>- Client: Response
```

## Notes

Place notes to the left, right, or spanning multiple participants.

```mermaid
sequenceDiagram
    participant A
    participant B
    Note left of A: Initiates call
    A ->> B: Hello
    Note right of B: Receives message
    Note over A,B: Shared context
```

## Loops

Repeat a block of interactions.

```mermaid
sequenceDiagram
    participant Poller
    participant API
    loop Every 5 seconds
        Poller ->> API: GET /status
        API -->> Poller: 200 OK
    end
```

## Alt / Else (Conditional)

Model branching based on a condition.

```mermaid
sequenceDiagram
    participant Client
    participant Auth
    Client ->> Auth: Login
    alt Credentials valid
        Auth -->> Client: 200 + token
    else Invalid credentials
        Auth -->> Client: 401 Unauthorized
    end
```

## Opt (Optional Fragment)

Show a block that executes only when a condition is met.

```mermaid
sequenceDiagram
    participant App
    participant Logger
    App ->> Logger: Log event
    opt Debug mode enabled
        Logger ->> Logger: Write stack trace
    end
```

## Par (Parallel)

Show concurrent execution paths.

```mermaid
sequenceDiagram
    participant Orchestrator
    participant ServiceA
    participant ServiceB
    par Parallel calls
        Orchestrator ->> ServiceA: Fetch data
    and
        Orchestrator ->> ServiceB: Fetch config
    end
    ServiceA -->> Orchestrator: Data
    ServiceB -->> Orchestrator: Config
```

## Critical / Option

Model a critical section with a mandatory body and optional fallback paths.

```mermaid
sequenceDiagram
    participant App
    participant DB
    critical Acquire lock
        App ->> DB: BEGIN TRANSACTION
    option Lock timeout
        App ->> App: Retry
    option Lock unavailable
        App -->> App: Raise error
    end
```

## Break

Exit a sequence early when a condition occurs.

```mermaid
sequenceDiagram
    participant Client
    participant Server
    Client ->> Server: Request
    break Request malformed
        Server -->> Client: 400 Bad Request
    end
    Server -->> Client: 200 OK
```

## Background Highlighting (rect)

Shade a region to group related interactions visually.

```mermaid
sequenceDiagram
    participant A
    participant B
    rect rgb(200, 220, 255)
        A ->> B: Step 1
        B -->> A: Ack
    end
    A ->> B: Step 2
```

## Sequence Numbering (autonumber)

Add automatic step numbers to all messages. Supports offset and increment.

```mermaid
sequenceDiagram
    autonumber
    participant Client
    participant Server
    Client ->> Server: POST /login
    Server -->> Client: 200 + token
    autonumber 10 2
    Client ->> Server: GET /profile
    Server -->> Client: 200 + profile
```

`autonumber` alone starts at 1 with increment 1. `autonumber <start> <step>` sets both.

## Links and Actor Menus

Attach clickable URLs to participants (renders as actor menu in supported renderers).

```mermaid
sequenceDiagram
    participant Alice
    participant Bob
    link Alice: Dashboard @ https://example.com/dashboard
    link Bob: Logs @ https://example.com/logs
    Alice ->> Bob: Hello
```

## v11+ Features

- `boundary`, `control`, `entity`, `queue`, `collections` participant types with UML icons
- Half-arrow message type: `A -| B: msg`
- Open back arrow: `A (- B: msg`
- Thick async arrows: `A ~>> B: msg` and `A ~~>> B: msg`

## Full Working Example

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Client as Web Client
    participant Server as API Server
    participant DB as Database

    User ->>+ Client: Click Submit
    Client ->>+ Server: POST /api/order

    critical Validate request
        Server ->> Server: Check schema
    option Invalid body
        Server -->> Client: 400 Bad Request
    end

    alt User authenticated
        Server ->>+ DB: INSERT order
        DB -->>- Server: order_id
        Server -->>- Client: 201 Created
    else Not authenticated
        Server -->>- Client: 401 Unauthorized
    end

    Client -->>- User: Show result

    note over Client,Server: All calls use TLS
```

## See Also

- [Flowchart Construction](./flowchart-construction.md)
- [Node Shapes](./node-shapes.md)
- [Edge Syntax](./edge-syntax.md)
- [Styling and Config](./styling-and-config.md)
- [Subgraphs and Layout](./subgraphs-and-layout.md)
