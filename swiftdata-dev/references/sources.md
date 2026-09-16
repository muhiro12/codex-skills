# Sources, availability, and provenance

Reviewed on 2026-09-16 against public Apple documentation, WWDC sessions, and
the Xcode 27.0 SDK. This date records the research baseline, not a promise that
APIs or documentation remain unchanged. Recheck exact declarations and platform
availability in the SDK used by the target project.

## Availability landmarks

| Feature family | iOS / macOS introduction | Official starting point |
| --- | --- | --- |
| SwiftData models, contexts, queries, schema migration, automatic CloudKit sync | iOS 17 / macOS 14 | [Meet SwiftData](https://developer.apple.com/videos/play/wwdc2023/10187/) |
| `#Index`, compound `#Unique`, persistent history, custom stores | iOS 18 / macOS 15 | [SwiftData updates](https://developer.apple.com/documentation/updates/swiftdata) |
| Persistent model inheritance | iOS 26 / macOS 26 | [Inheritance and schema migration](https://developer.apple.com/videos/play/wwdc2025/291/) |
| Sectioned query macros, `.codable`, `ResultsObserver`, `HistoryObserver` | iOS 27 / macOS 27 | [What's new in SwiftData](https://developer.apple.com/videos/play/wwdc2026/274/) |

These are feature-family landmarks, not availability for every overload or
other platform. A new compiler does not make newer runtime APIs available on
older deployment targets. Check related Observation APIs independently.

## Read by the implementation question

- Container/configuration and context behavior:
  [Dive deeper into SwiftData](https://developer.apple.com/videos/play/wwdc2023/10196/),
  [ModelContext](https://developer.apple.com/documentation/swiftdata/modelcontext),
  [concurrency support](https://developer.apple.com/documentation/swiftdata/concurrencysupport).
- Schema evolution and Core Data mapping:
  [Model your schema with SwiftData](https://developer.apple.com/videos/play/wwdc2023/10195/),
  [Migrate to SwiftData](https://developer.apple.com/videos/play/wwdc2023/10189/).
- Query tuning and change consumption:
  [WWDC24 updates](https://developer.apple.com/videos/play/wwdc2024/10137/),
  [persistent history](https://developer.apple.com/videos/play/wwdc2024/10075/).
- Framework wiring and practical questions:
  [Code-along: Add persistence with SwiftData](https://developer.apple.com/videos/play/wwdc2026/275/),
  [SwiftData Group Lab](https://developer.apple.com/videos/play/wwdc2026/8017/).
- Automatic sync and schema limitations:
  [Syncing model data across a person's devices](https://developer.apple.com/documentation/swiftdata/syncing-model-data-across-a-persons-devices).

Follow sample links from those official pages when implementation wiring needs
clarification. Check the downloaded project's SDK, schema, and error handling
before applying it. Presentation snippets can be abbreviated or contain errors;
compile against the actual SDK instead of treating a transcript as a signature.
Public documentation or locally exported Xcode guidance may be newer than this
skill; inspect the relevant source rather than extrapolating an API.

Custom stores and a wholesale Core Data migration need their own scoped design.
The presence of those capabilities is not a reason to introduce them into an
ordinary SwiftData feature.

## Admit evidence at its demonstrated strength

- Use current documentation and SDK declarations for supported APIs and
  availability; check store-specific restrictions independently.
- Use release notes for the issue and fix actually named. A historical fixed
  issue is not proof that a present failure has the same cause. Distinguish beta
  development from released OS versions; preserve the exact affected build when
  available instead of assigning a bug to an entire major release.
- Attribute Apple staff/DTS answers explicitly. Other posts on Apple or Swift
  forums remain community reports unless independently confirmed.
- Use first-person articles, public patches, and reproductions for conditions,
  attempted mitigation, and observed outcome. Separate the author's diagnosis
  from what the evidence establishes; an emphatic headline is not a contract.
- Treat recollections, inaccessible posts, and unspecified versions as leads.
  Do not invent a current restriction or successful workaround from them.

See [compatibility.md](compatibility.md) for restrictions, changed availability,
and scoped synthetic checks. Read the linked primary source before strengthening
an incident's status. A later successful probe does not establish a fix date.

For retrospective diagnosis, separate the existence of a reported failure from
the cause of a particular application's incident. Compare contemporaneous code,
store definitions, diagnostics, and toolchain details. A missing old artifact
leaves the cause unresolved; it is not evidence of either developer error or a
framework defect. Conversely, a supported API contract does not prove that its
implementation worked for every configuration at the time.

## Authorship and reuse

The short entrypoint and topic-specific references were informed by Xcode's
exported specialist skills and
[d-date/iphone-duo-skill](https://github.com/d-date/iphone-duo-skill).
That community repository is a structural reference, not a SwiftData authority.
This skill does not redistribute those skills, Apple transcripts, or sample code.

The topic references summarize linked Apple APIs and their immediate implications
for implementation and diagnosis, with explicitly labeled first-person reports
where they add diagnostic evidence. The separate [incident reference](known-issues.md)
records public application failures and attempted mitigations, with per-case
evidence and limits. It does not promote application architecture choices to
SwiftData requirements. Historical reports are not current runtime verification.

The skill requires no particular domain model, use-case layer, draft system,
backup format, or synchronization strategy. Private app data, logs, local paths,
account/container identifiers, and unpublished decisions are not included.
