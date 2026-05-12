# Swift Code Rubric

Use this rubric for Swift creation, audit, and repair. The goal is not to make every file look identical; it is to make Swift code clear at the use site, type-safe, concurrency-safe, maintainable, and aligned with official Swift guidance.

## Severity

- `blocking`: A compiler error, data-race risk, actor-isolation violation, public API trap, package boundary break, persistence-affecting semantic change, or high-confidence behavioral bug.
- `warning`: Code works but is non-idiomatic, unclear at call sites, weakly typed, concurrency-fragile, hard to test, package-boundary unclear, or likely to drift under Swift 6 checking.
- `note`: A polish, documentation, naming, coverage, or tradeoff observation that does not need to block the current change.

## Checks

### 1. API Design and Naming

- Create: Design from call sites. Prefer clear usage over brevity, role-based names over type-repeating names, and argument labels that clarify weakly typed values.
- Audit: Look for ambiguous base names, needless words, unlabeled weak types, non-fluent call sites, overloaded return-type ambiguity, and inconsistent mutating/nonmutating names.
- Fix: Rename and relabel APIs locally when safe; for public APIs, update call sites, documentation, and compatibility notes together.

### 2. Language Semantics and Type Modeling

- Create: Model invalid states out of existence with enums, optionals, result types, access control, and narrow initializers where appropriate.
- Audit: Check force unwraps, implicitly unwrapped optionals, stringly typed states, broad `Any`, leaky access levels, and behavior hidden in computed properties.
- Fix: Tighten types and access control without changing product semantics.

### 3. Value and Reference Semantics

- Create: Prefer value types for independent data and reference types for shared identity, lifecycle, observation, or actor-isolated mutation.
- Audit: Check accidental shared mutable state, classes used as plain data bags, structs hiding expensive copy or identity assumptions, and unclear ownership.
- Fix: Choose `struct`, `class`, `actor`, or `enum` based on identity, mutation, ownership, and concurrency needs.

### 4. Concurrency and Data-Race Safety

- Create: Define isolation before adding async work. Use actors, `@MainActor`, `Sendable`, structured tasks, cancellation, and async sequences deliberately.
- Audit: Check unstructured `Task` lifetimes, missing cancellation, actor boundary leaks, non-Sendable captured state, shared mutable state, and UI work outside the main actor.
- Fix: Prefer structured concurrency, explicit isolation, sendable-safe data transfer, and cancellation-aware APIs.

### 5. Error Handling and Optionality

- Create: Use `throws`, typed domain errors, optionals, and result modeling according to the caller's recovery needs.
- Audit: Look for swallowed errors, sentinel values, optional ambiguity, overbroad `catch`, fatal errors in recoverable paths, and unclear async failure surfaces.
- Fix: Make failure modes visible and testable while keeping user-facing behavior stable.

### 6. Generics, Protocols, and Existentials

- Create: Use generics when the caller should preserve static type information; use protocols for behavior contracts; use `any` existentials or type erasure intentionally.
- Audit: Check protocol overuse, associated-type complexity leaking into simple code, needless type erasure, and generic constraints that obscure the domain model.
- Fix: Simplify abstractions unless they remove real duplication, protect a boundary, or express stable domain behavior.

### 7. Standard Library and Core Libraries Fit

- Create: Prefer standard library, Foundation, and Swift Core Libraries APIs before introducing custom equivalents.
- Audit: Look for hand-rolled collection operations, date/string/path handling, inefficient algorithms hidden behind properties, and missed standard protocols.
- Fix: Replace custom code with well-known Swift APIs when it improves correctness, clarity, or performance.

### 8. Packages, Modules, and Access Control

- Create: Keep package targets cohesive, dependencies directional, access levels narrow, and test-only helpers out of production targets.
- Audit: Check `Package.swift` drift, circular or leaky dependencies, overly public declarations, app-specific concepts in shared libraries, and durable logic trapped in app targets.
- Fix: Adjust target boundaries conservatively and keep package-level changes tied to the current task.

### 9. Documentation and DocC

- Create: Document public and reusable declarations when the summary clarifies behavior, complexity, concurrency, throwing behavior, preconditions, or examples.
- Audit: Check undocumented public API, misleading comments, missing complexity notes for non-O(1) properties, and comments that repeat the signature.
- Fix: Add concise documentation comments that improve API understanding at the call site.

### 10. Verification and Migration Risk

- Create: Add tests near durable logic, boundary behavior, and concurrency or error cases.
- Audit: Check whether the change is covered by library tests, package tests, app builds, or concurrency checking.
- Fix: Run targeted checks first, then the repository's standard verification gate; call out unverified Swift version, platform, or toolchain assumptions.

## Review Questions

Ask these before concluding Swift code is aligned:

- Is the API clear where it is used, not just where it is declared?
- Does the type model prevent invalid states or merely document them?
- Is mutable shared state isolated, sendable, or otherwise concurrency-safe?
- Are package and access boundaries narrower than the implementation detail they expose?
- Would Swift 6 complete concurrency checking make this code more trustworthy or reveal problems?
- Can every finding be tied to code evidence, compiler diagnostics, tests, package structure, or an official Swift source?
