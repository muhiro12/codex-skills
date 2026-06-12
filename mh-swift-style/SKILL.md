---
name: mh-swift-style
description: Apply Hiromu/MH local Swift style preferences when creating, editing, refactoring, or reviewing Swift code in Hiromu's Apple-platform repositories. Use when Swift code generation or review should preserve MH-style preferences such as clear non-abbreviated names, `.init(...)` for explicit return types, multiline control-flow bodies, and existing repository source style, while still respecting official Swift guidance, compiler diagnostics, SwiftLint, and repository-specific rules.
---

# MH Swift Style

## Overview

Use this skill as the local style layer for Swift work in Hiromu/MH
repositories. These preferences are strong local standards, not casual
suggestions, but they do not override compiler correctness, official Swift
guidance, repository architecture, SwiftLint, or explicit user instructions.

## Source Order

Apply style decisions in this order:

1. Explicit current user instructions.
2. Compiler correctness, Swift language semantics, and SwiftLint.
3. Repository `AGENTS.md`, architecture documents, and existing source style.
4. Official Swift guidance and `$swift-code-guardian` when the task involves
   API shape, public/reusable code, concurrency, type modeling, or package
   boundaries.
5. The MH local style preferences below.

If this skill conflicts with official Swift clarity, safety, concurrency
correctness, public API usability, or a repository-local rule, name the conflict
and follow the stronger source.

## Core Preferences

### Prefer Clear Names

Use clear, complete names for local variables, properties, functions, and
types. Avoid abbreviated names unless the abbreviation is a well-established
Swift or domain term already used in the repository.

Prefer:

- `result`
- `image`
- `button`

Avoid:

- `res`
- `img`
- `btn`

### Prefer `.init(...)` When the Type Is Explicit

Use `.init(...)` when the return type or assigned type is already explicit and
the initializer call remains clear.

Prefer:

```swift
var user: User {
    .init(name: "Alice")
}
```

Avoid:

```swift
var user: User {
    User(name: "Alice")
}
```

Do not force `.init(...)` when the explicit type name improves readability,
disambiguates overloads, clarifies a complex generic, or matches a strong
nearby repository pattern.

### Prefer Multiline Control Flow

Do not use single-line bodies for control-flow statements or trailing closures
in repository code. Keep early returns, `if`, `guard`, `switch`, loops, and
closure bodies readable on multiple lines.

Prefer:

```swift
guard let currentUser else {
    return
}

if isDebugMode {
    logger.debug("Entering debug state")
}

tasks.filter { task in
    task.isCompleted
}
```

Avoid:

```swift
guard let currentUser else { return }
if isDebugMode { logger.debug("Entering debug state") }
tasks.filter { $0.isCompleted }
```

Exception: follow standard Swift shorthand for tiny expression closures only
when it is already the local pattern and does not reduce clarity.

## Usage

- Use this skill after reading the affected repository code so style choices
  follow the local source, not a generic template.
- Apply these preferences during creation and cleanup, not only after review.
- Prefer fixing style drift in touched code when it is local and low risk.
- Avoid broad style-only rewrites outside the current task scope.
- If the repository has a formatter or SwiftLint autofix command, run it before
  final verification when Swift files were edited.

## Output

When this skill materially affects a change or review, mention the style choice
briefly in Japanese, especially when choosing not to apply a preference because
a stronger source overrides it.
