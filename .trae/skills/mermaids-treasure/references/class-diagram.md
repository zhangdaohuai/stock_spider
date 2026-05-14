> Parent: [Mermaid Diagram Syntax](../SKILL.md)

# Class Diagram Syntax Reference

Complete syntax reference for Mermaid `classDiagram` diagrams — class definitions, visibility modifiers, relationship types, cardinality, generics, annotations, namespaces, notes, direction, and links.

## Declaration

```mermaid
classDiagram
    class Animal {
        +String name
        +makeSound()
    }
```

The keyword `classDiagram` opens the diagram. No direction qualifier is required at the declaration line — set direction with `direction` inside the body.

## Class Definition

Two forms are valid:

```mermaid
classDiagram
    class ClassName

    class Name {
        +name: string
        +age: int
        +getName() string
        +getAge() int
    }
```

The bare form (`class ClassName`) declares a class with no members. The block form uses `{}` to list attributes and methods. Type annotations follow the member name after a colon or space, and return types follow the method signature.

## Attributes and Methods

```mermaid
classDiagram
    class Account {
        +String owner
        -float balance
        #String currency
        ~int internalCode
        +deposit(amount) void
        -validate(amount) bool
        #log(event)
        $int instanceCount
        *abstract()
    }
```

Visibility prefixes:

| Prefix | Visibility |
|--------|-----------|
| `+` | Public |
| `-` | Private |
| `#` | Protected |
| `~` | Package / Internal |
| `$` | Static (attribute or method) |
| `*` | Abstract (method only) |

Methods use `()` after the name. Parameters go inside the parens. Return type follows the closing paren.

## Relationship Types

```mermaid
classDiagram
    Animal <|-- Dog
    Vehicle *-- Engine
    Company o-- Employee
    Student --> School
    Car ..> Fuel
    Shape ..|> Drawable
    ClassA -- ClassB
```

| Syntax | Relationship | Meaning |
|--------|-------------|---------|
| `<\|--` | Inheritance | Subclass extends superclass |
| `*--` | Composition | Strong ownership; child cannot exist without parent |
| `o--` | Aggregation | Weak ownership; child can exist independently |
| `-->` | Association | General directed relationship |
| `..>` | Dependency | One class uses another |
| `..\|>` | Realization | Class implements an interface |
| `--` | Link | Undirected solid line |

Arrow direction can be reversed: `Dog --|> Animal` produces the same inheritance as `Animal <|-- Dog`.

## Relationship Labels and Cardinality

```mermaid
classDiagram
    Vehicle "1" *-- "1..*" Wheel : has
    Customer "1" --> "*" Order : places
    Person "1" --> "0..1" Passport : holds
```

Cardinality strings go in double quotes on each side of the relationship operator. A label string follows a colon after the operator.

Common cardinality values: `1`, `*`, `0..1`, `1..*`, `0..*`, `n`.

## Generic Types

```mermaid
classDiagram
    class Container~T~ {
        +T value
        +get() T
        +set(T item)
    }

    class Pair~K, V~ {
        +K key
        +V value
    }
```

Generic type parameters use `~T~` syntax on the class name. Multiple parameters are comma-separated inside the tildes.

## Annotations

Annotations render as stereotypes inside the class box.

```mermaid
classDiagram
    class PaymentService {
        <<Service>>
        +processPayment(amount)
    }

    class Printable {
        <<Interface>>
        +print() void
    }

    class Shape {
        <<Abstract>>
        *area() float
    }

    class Color {
        <<Enumeration>>
        RED
        GREEN
        BLUE
    }

    class Entity {
        <<Entity>>
        +int id
    }
```

Built-in annotations: `<<Interface>>`, `<<Abstract>>`, `<<Service>>`, `<<Enumeration>>`, `<<Entity>>`. Custom annotation strings are also valid — any text inside `<< >>` renders as a stereotype label.

## Notes

```mermaid
classDiagram
    class BankAccount {
        +String owner
        +float balance
        +deposit(amount)
    }

    note "This is a domain model class"
    note for BankAccount "Balance must always be >= 0"
```

`note "text"` adds a floating note. `note for ClassName "text"` attaches the note to a specific class.

## Direction

```mermaid
classDiagram
    direction LR

    class A
    class B
    A --> B
```

Valid values: `TB` (top-to-bottom, default), `BT` (bottom-to-top), `LR` (left-to-right), `RL` (right-to-left). Place the `direction` statement at the top of the diagram body.

## Links and Click Events

```mermaid
classDiagram
    class Shape {
        +area() float
    }

    link Shape "https://example.com/shape" "Tooltip text"
    click Shape href "https://example.com/shape" "Tooltip text"
    click Shape call myCallback()
```

`link` adds a hyperlink to the class. `click ... href` adds a clickable link with tooltip. `click ... call` binds a JavaScript callback. Click interactivity requires `securityLevel='loose'` in the renderer configuration.

## Namespaces

```mermaid
classDiagram
    namespace Geometry {
        class Point {
            +int x
            +int y
        }
        class Line {
            +Point start
            +Point end
        }
    }

    namespace Animals {
        class Dog
        class Cat
    }

    Point --> Line : used by
    Dog --|> Cat
```

`namespace Name { ... }` groups classes visually. Cross-namespace relationships use the plain class names — no namespace prefix is needed in the relationship syntax.

## Complete Example

```mermaid
classDiagram
    direction TB

    class Animal {
        <<Abstract>>
        -String name
        -int age
        +getName() String
        +getAge() int
        *makeSound() void
    }

    class Dog {
        -String breed
        +getBreed() String
        +bark() void
    }

    class Cat {
        -String color
        +getColor() String
        +meow() void
    }

    class Owner {
        -String name
        +adoptPet(Animal) void
    }

    class IPet {
        <<Interface>>
        +feed() void
        +play() void
    }

    Animal <|-- Dog
    Animal <|-- Cat
    Dog ..|> IPet
    Cat ..|> IPet
    Owner "1" o-- "*" Animal : owns

    note for Animal "Base class for all animals"
```

## v11+ Features

Mermaid v11 introduced `classDiagram-v2` as an alias — identical syntax to `classDiagram`. No behavioral difference; both keywords produce the same output.

SOURCE: [Mermaid Class Diagram Documentation](https://mermaid.js.org/syntax/classDiagram.html) (accessed 2026-03-07)

## See Also

- [Flowchart Syntax](../SKILL.md)
- [State Diagram](./state-diagram.md)
- [ER Diagram](./er-diagram.md)
- [Sequence Diagram](./sequence-diagram.md)
