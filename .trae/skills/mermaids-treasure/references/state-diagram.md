> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# State Diagram

**Declaration**: `stateDiagram-v2` (preferred) or `stateDiagram` (v1, legacy)

Use `stateDiagram-v2` for all new diagrams — it supports composite states, concurrency, fork/join, and direction control that v1 lacks.

## Start and End States

`[*]` is the pseudo-state used for both start (initial) and end (final) depending on position.

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> [*]
```

## Simple States and Transitions

```mermaid
stateDiagram-v2
    State1 --> State2
    State2 --> State1 : Transition label
```

Transition labels follow the `:` separator. Labels are optional.

## Composite (Nested) States

Wrap child states in a `state Name { }` block.

```mermaid
stateDiagram-v2
    state Active {
        [*] --> Running
        Running --> Paused
        Paused --> Running : Resume
        Paused --> [*]
    }

    [*] --> Active
    Active --> [*]
```

Composite states can be nested to arbitrary depth.

## Fork and Join

Use `<<fork>>` to split into parallel paths and `<<join>>` to merge them.

```mermaid
stateDiagram-v2
    [*] --> Fork1
    state Fork1 <<fork>>
    Fork1 --> BranchA
    Fork1 --> BranchB

    BranchA --> Join1
    BranchB --> Join1
    state Join1 <<join>>
    Join1 --> [*]
```

## Concurrency

The `---` separator inside a composite state declares concurrent (parallel) regions.

```mermaid
stateDiagram-v2
    state Parallel {
        [*] --> RegionA
        RegionA --> [*]
        --
        [*] --> RegionB
        RegionB --> [*]
    }

    [*] --> Parallel
    Parallel --> [*]
```

Each region separated by `---` runs independently.

## Choice (Conditional Branch)

```mermaid
stateDiagram-v2
    [*] --> CheckInput
    state CheckInput <<choice>>
    CheckInput --> Valid : input ok
    CheckInput --> Invalid : input bad
    Valid --> [*]
    Invalid --> [*]
```

## Notes

Attach a note to any state using `note right of` or `note left of`.

```mermaid
stateDiagram-v2
    [*] --> Working
    Working --> Done

    note right of Working
        Processing in progress.
        May take several seconds.
    end note
```

## Direction

Control layout with the `direction` keyword. Place it at the top of the diagram or inside a composite state.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> A
    A --> B
    B --> [*]
```

Valid values: `TB` (top-bottom, default), `BT`, `LR`, `RL`.

## v11+ Features

- `stateDiagram-v2` is fully supported in v11; `stateDiagram` (v1) remains available for legacy use
- Per-state styling via `classDef` and `:::` inline syntax
- Composite state direction overrides (each nested state can have its own `direction`)

```mermaid
stateDiagram-v2
    classDef errorStyle fill:#f44,color:white
    Error:::errorStyle

    [*] --> Running
    Running --> Error : exception
    Error --> [*]
```

## Complete Example

```mermaid
stateDiagram-v2
    direction LR

    [*] --> Idle

    Idle --> Working : Start
    Working --> Paused : Pause
    Paused --> Working : Resume
    Working --> Completed : Finish

    Paused --> Idle : Cancel
    Working --> Error : Exception
    Error --> Idle : Reset

    Completed --> [*]
    Idle --> [*] : Exit

    note right of Working
        Processing task
    end note
```

## See Also

- [Flowchart Syntax](../SKILL.md)
- [Class Diagram](./class-diagram.md)
- [ER Diagram](./er-diagram.md)
