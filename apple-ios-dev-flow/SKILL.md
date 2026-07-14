---
name: apple-ios-dev-flow
description: Orchestrate Apple-platform app development in this local Codex/Xcode environment by routing implementation, refactor, UI, Swift, sample-code, simulator, App Intents, performance, leak, preview, smoke, and verification work across Hiromu's custom skills, the active Xcode-native integration, selectively compatible OpenAI Build iOS Apps skills, Apple official guidance, repo-local evidence, and the repository's documented verification contract.
---

# Apple iOS Dev Flow

## Overview

Use this skill as the default entrypoint and orchestrator for ordinary Apple-platform implementation requests in this PC environment.
Keep the workflow core in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Return user-facing explanations in concise, practical Japanese.
Keep code, commands, file names, identifiers, and repository documents in English unless the target repository already uses another convention.
Treat this skill as the place that chooses evidence, gates, and specialist skills. Do not duplicate the detailed implementation procedures from sidecar skills; route to them when their trigger is a better fit.
When implementation depends on recurring cross-repository judgment, consult a local principle archive skill when available (for example `$track-developer-principles`) before settling the approach.
When a matching Xcode-provided skill exists, prefer it as the first Apple/Xcode guidance source.
When a related Apple sample may show the concrete implementation shape for the framework, app shell, lifecycle, target boundary, entitlement, cross-surface feature, SwiftUI composition, model/data wiring, or system integration at hand, use `$apple-sample-code-advisor` early after matching Xcode-provided skill guidance.
When implementation affects user interface, navigation, controls, visual hierarchy, accessibility, platform adaptation, or Apple design-system behavior, use `$apple-hig-ui-guardian` before settling or preserving the UI shape.
When implementation affects Swift APIs, naming, type modeling, concurrency, `Sendable`, actor isolation, package/module boundaries, access control, public documentation, or SwiftPM manifests, use `$swift-code-guardian` before settling or preserving the code shape.
When Swift implementation or review should preserve Hiromu/MH local source style, use `$mh-swift-style` after repository evidence and Swift correctness constraints are clear.
Use the active Xcode-native tool surface for build, test, run, Preview, logs,
and device interaction. Resolve actions by capability from the current tool
inventory instead of assuming a namespace or action spelling. Use an OpenAI
Build iOS Apps skill only when the skill is relevant and every tool namespace
it requires is present in the current tool inventory; otherwise keep the
Xcode-native workflow and report the unavailable specialist as an optional
compatibility gap. Treat the repository's documented verification contract as
the final readiness gate.
When `sync-xcode-skills/state/catalog.md` exists under the active Codex skills root, treat it as the local catalog of Xcode-provided Skills. Use it to discover currently installed `xcode-skill-*` guidance instead of hardcoding Xcode-provided skill names.

## Trigger Conditions

Use this skill when the user asks to implement, fix, refactor, review, debug, profile, audit, or continue work in an Apple-platform repository and no more specific sidecar skill is a better direct entrypoint.

Prefer specialized skills instead for:

- string catalog maintenance
- SwiftUI preview audits
- HIG-specific UI creation, audit, or repair requests
- Swift-specific API, concurrency, package, or language-semantics work
- Apple sample-code research, cache, refresh, or sample-backed architecture comparison requests
- SwiftData schema audits
- release-risk reviews
- release notes
- repository verification bootstrap or repair

## Local Environment Surfaces

Assume these surfaces are available in this Codex desktop environment when the active tool and skill lists show them:

- Hiromu custom skills: `$track-developer-principles`, `$apple-hig-ui-guardian`, `$swift-code-guardian`, `$mh-swift-style`, `$apple-sample-code-advisor`, `$xcode-preview-auditor`, `$xcode-ui-smoke-auditor`, `$ci-verify-and-summarize`, and repository workflow skills.
- OpenAI Build iOS Apps skills: `$build-ios-apps:swiftui-ui-patterns`, `$build-ios-apps:swiftui-view-refactor`, `$build-ios-apps:swiftui-liquid-glass`, `$build-ios-apps:swiftui-performance-audit`, `$build-ios-apps:ios-app-intents`, `$build-ios-apps:ios-debugger-agent`, `$build-ios-apps:ios-ettrace-performance`, `$build-ios-apps:ios-memgraph-leaks`, and `$build-ios-apps:ios-simulator-browser`. Treat a skill that depends on a missing tool namespace as unavailable rather than translating its calls by guesswork.
- Local Apple sample cache: `apple-sample-code-advisor/cache` under the active Codex skills root, managed through `$apple-sample-code-advisor`. Resolve the active root from the loaded skill paths, or `${CODEX_HOME:-$HOME/.codex}/skills` only when the loaded path is unavailable.
- Generated Xcode-provided Skill catalog: `sync-xcode-skills/state/catalog.md` under the active Codex skills root, managed through `$sync-xcode-skills`.
- The active Xcode-native integration for workspace discovery and active
  selection, build, test, run, logs, Preview rendering, and device interaction.
- Repository verification contracts, especially `AGENTS.md`, Xcode-native
  build/test/run expectations, and retained `ci_scripts` format, lint,
  static-rule, or otherwise uncovered checks.
- Local sibling repositories only as read-only fallback evidence after stronger Apple and current-repo sources.

## Decision Order

1. Start from current repository evidence.
- Read the affected code, tests, diagnostics, `AGENTS.md`, and `ci_scripts` first.
- Preserve the repository's better Apple-appropriate pattern when it is already clear.

2. Use a local principle archive skill second when judgment matters.
- Consult it when the task depends on tradeoffs such as maintainability, architecture direction, product intent, workflow philosophy, naming heuristics, or quality bars that may repeat across repositories.
- If stored principles point to a maintained platform foundation such as a resolved local MHPlatform checkout for shared stack, reusable plumbing, or cross-app implementation direction, treat that as part of the current decision context before falling back to a generic sibling reference repository.
- Treat explicit current-task instructions and hard repository constraints as higher priority than older archived principles when they conflict.

3. Check Xcode-provided Skill guidance when present.
- If the generated Xcode Skill catalog exists, scan it before local Apple specialist routing for task-specific Xcode guidance.
- If a listed `xcode-skill-*` clearly matches the current Apple-platform issue, use that Skill before applying local custom-skill heuristics.
- Do not hardcode individual Xcode-provided Skill names in this orchestrator; let `$sync-xcode-skills` keep the catalog current.
- If the catalog is missing or no listed skill matches, continue through the normal local gates.

4. Use Apple sample code when a related sample may clarify implementation.
- For framework adoption, app architecture, lifecycle, target boundaries, entitlements, cross-surface implementation, SwiftUI app composition, model/data wiring, or system integration, invoke `$apple-sample-code-advisor` after matching Xcode-provided skill guidance.
- Treat related sample projects as concrete implementation evidence that usually clarifies shape better than prose documentation alone, while still subordinate to explicit product constraints, HIG, Swift language guidance, and framework API documentation.

5. Apply the HIG gate for UI-affecting work.
- For changes that affect user-visible Apple UI, invoke `$apple-hig-ui-guardian` and read its rubric before editing or approving the UI shape.
- Treat HIG and current Apple official design guidance as active constraints, not only as fallback references when the implementation is unclear.
- Preserve local UI conventions only when they remain compatible with HIG; name intentional product-driven departures from HIG.

6. Apply the Swift code gate for Swift-language work.
- For changes that affect Swift APIs, package boundaries, concurrency, type modeling, documentation, or public/reusable code, invoke `$swift-code-guardian` and read its rubric before editing or approving the code shape.
- Treat official Swift documentation, API Design Guidelines, and concurrency guidance as active constraints, not only as fallback references when the implementation is unclear.
- Preserve local Swift style only when it remains compatible with Swift clarity, safety, and language semantics.
- For ordinary Swift implementation style after the Swift correctness gate, invoke `$mh-swift-style` when available to preserve Hiromu/MH local preferences such as clear names, `.init(...)` for explicit types, and multiline control flow.

7. Use Apple and Swift official guidance next.
- Prefer Apple documentation, Swift.org documentation, Human Interface Guidelines, WWDC material, Swift API Design Guidelines, and Swift language guidance when they define requirements, API contracts, or language behavior.
- Prefer Apple or Swift official guidance over general web advice.

8. Route execution to OpenAI Build iOS Apps specialist skills when they match the task.
- Use specialist skills for concrete SwiftUI, App Intents, simulator, performance, ETTrace, or leak workflows after the current-repo and official-guidance gates establish the intended direction.
- Treat specialist workflow guidance as implementation help; do not let it override explicit product constraints, HIG, Swift language guidance, framework documentation, or current Apple sample evidence.

9. Use a locally available sibling reference repository last as a read-only fallback.
- If a locally available sibling reference repository is available and relevant, inspect it only after current-repo evidence plus Apple, Swift, and sample-code official guidance still do not settle the approach.
- Borrow reusable workflow or architecture intent, not app-specific UX, domain models, or naming.

## Specialist Routing

Use this routing before editing when a sidecar skill can narrow the work:

- General SwiftUI screen or component creation: use `$apple-hig-ui-guardian`, then `$build-ios-apps:swiftui-ui-patterns`; add `$swift-code-guardian` when API shape or state modeling matters.
- SwiftUI view cleanup or body decomposition: use `$build-ios-apps:swiftui-view-refactor`, plus `$swift-code-guardian` for Observation, dependency injection, access control, and concurrency boundaries.
- Liquid Glass work: use `$apple-hig-ui-guardian`, `$build-ios-apps:swiftui-liquid-glass`, and `$apple-sample-code-advisor` for current Landmarks-style sample evidence when project-level shape matters.
- App Intents, App Entities, App Shortcuts, Siri, Spotlight, widgets, or controls integration: use `$build-ios-apps:ios-app-intents`, plus `$swift-code-guardian` for API and concurrency quality.
- Simulator run, UI interaction, runtime logs, screenshots, or live debugging:
  use the Xcode-native capability selection and execution contract below.
  Follow a matching generated Xcode skill discovered from the catalog. Use
  `$build-ios-apps:ios-debugger-agent` only as an optional fallback when its
  documented tool namespace and exact tools exist in the current inventory.
- Browser-visible Simulator mirroring or Swift Package Preview hot reload: use `$build-ios-apps:ios-simulator-browser` when the user asks for that interactive browser workflow and its runtime dependencies are available; do not substitute it for native Preview or UI audit evidence by default.
- SwiftUI performance diagnosis from code: use `$build-ios-apps:swiftui-performance-audit`; use `$build-ios-apps:ios-ettrace-performance` when runtime trace evidence is required.
- Memory growth, retain cycles, or leak proof: use
  `$build-ios-apps:ios-memgraph-leaks` when its required tools exist, paired
  with the active Xcode-native runtime lifecycle for live app setup. Use
  `$build-ios-apps:ios-debugger-agent` only when its separate required
  namespace also exists.
- Preview-based visual audit: use `$xcode-preview-auditor`, then `$apple-hig-ui-guardian` for HIG classification of any issues.
- Live release UI smoke or screenshot audit: use `$xcode-ui-smoke-auditor`, then `$apple-hig-ui-guardian` for UI/design-system findings.
- Related Apple sample exists or likely exists for framework adoption, lifecycle, target layout, entitlements, cross-surface features, SwiftUI composition, model/data wiring, or modern app shell decisions: use `$apple-sample-code-advisor` after matching Xcode-provided skill guidance and before relying on prose documentation alone or sibling repository fallback.
- Final verification and diff summary: use `$ci-verify-and-summarize` when the repository provides a shell or retained repository-rule entrypoint and the user asks for verify/CI/push-readiness summarization; otherwise run the documented MCP checks and retained rule checks directly.

## Xcode-Native Capability Selection And Execution Contract

Use this lifecycle with the Xcode-native capabilities present in the current
tool inventory. Treat concrete namespaces, action names, parameter keys, and
response fields as replaceable adapter details rather than durable policy.

1. Use the available workspace/project discovery capability to identify the
   Xcode context that matches the current repository. Do not guess when more
   than one context is open.
2. Discover the active and available schemes and destinations. Record the
   original scheme and destination, including whatever unambiguous handles the
   current integration returns for reliable restoration.
3. Keep the active selection when it satisfies the repository contract.
   Otherwise switch only to values returned by discovery, refresh destinations
   after a scheme switch, and remember that the integration may automatically
   change the destination.
4. Choose the narrow capability that proves the changed boundary: a surface
   build, all or targeted tests, a bounded run with logs and stop, direct
   Preview rendering, or a bounded live UI session with screenshots,
   hierarchy, logs, orientation, and interactions.
5. End every interaction session and stop a run started solely for
   verification. If the workflow changed Xcode's active selection, restore the
   original scheme first and its original destination second, then rediscover
   both to confirm. If restoration is unsafe or impossible, report the final
   active selection explicitly.

If one required capability is absent, report that gap and use only a
repository-documented fallback. Never infer a renamed action or translate a
missing third-party namespace by guesswork.

Never invent an adapter for a missing third-party MCP namespace. A Build iOS Apps skill that documents a different namespace is optional guidance only when that namespace and its exact tools are actually available.

## Verification Evidence Selection

Use the repository `AGENTS.md` as the source of concrete schemes, packages,
scripts, and surfaces, then choose verification evidence by the changed
boundary:

- Shared-library or package logic changes: run the documented library/package
  tests and retained repository-rule checks. Add an app or example build when
  the change affects public APIs, `*Operations`, persisted schema, route or wire
  contracts, package products, or adopter-facing integration.
- App, widget, watch, extension, App Intent, or UI-adapter-only changes: run the
  documented build for the changed surface. Run shared-library tests only when
  the shared contract or reusable behavior changed.
- Mixed library plus surface changes: run both the relevant library/package
  tests and the affected surface builds.
- Runtime, navigation, visible UI, lifecycle, entitlement, persistence,
  notification, sync, widget timeline, watch connectivity, App Intent, or
  framework-integration risk: add targeted simulator launch, logs, UI snapshot,
  screenshot, preview, smoke, or specialist evidence instead of treating live UI
  checks as a default for every change.
- If the change scope is uncertain, choose the stronger evidence set and say
  which boundary made the narrower check insufficient.

Do not copy this decision model into every repository `AGENTS.md`. Repository
contracts should expose the concrete verification capabilities needed from a
fresh clone; this skill should choose among them in Hiromu's local environment.

## Workflow

1. Confirm repository workflow prerequisites.
- Resolve the repository's documented verification contract from `AGENTS.md` first, then `ci_scripts/**/*.sh`, then repo-native aggregate commands.
- When `AGENTS.md` specifies Xcode-native build/test/run expectations, resolve
  and execute those capabilities directly instead of looking for an equivalent
  custom shell.
- If the repository provides an explicit repo-managed autofix step for edited files such as `format_swift.sh`, treat it as part of the main implementation flow before the final verification gate.
- If the repository does not have a coherent verification contract, switch to `$apple-repo-verify-bootstrapper` or tell the user that the repo needs that scaffolding first.
- For simulator execution or UI/debug validation, follow the Xcode-native
  capability selection and execution contract above, including
  original-selection capture and restoration, then run retained repository
  rule checks when they are documented.

2. Implement with local evidence first.
- Inspect the target files, adjacent tests, and current diagnostics before editing.
- Keep the patch as small and local as the task allows.
- For UI-affecting changes, use `$apple-hig-ui-guardian` to choose or review the UI approach before preserving local visual patterns.
- For Swift-affecting changes, use `$swift-code-guardian` to choose or review API shape, type modeling, concurrency, documentation, package, and access-control decisions before preserving local code patterns.
- For framework adoption, app shell, lifecycle, target-boundary, cross-surface features, SwiftUI composition, model/data wiring, or system integrations with a related Apple sample, use `$apple-sample-code-advisor` after matching Xcode-provided skill guidance and before borrowing from prose-only documentation or a sibling repository.

3. Make implementation decisions in this order.
- current repository evidence
- a local principle archive skill when available and the decision is judgment-heavy
- generated Xcode-provided Skill catalog when present and task-relevant
- `$apple-sample-code-advisor` when related Apple sample source can clarify the implementation shape
- `$apple-hig-ui-guardian` for UI-affecting work
- `$swift-code-guardian` for Swift-language, API, concurrency, or package-boundary work
- Apple official guidance
- Swift official guidance
- OpenAI Build iOS Apps specialist skills for task-specific implementation workflow
- a locally available sibling reference repository read-only fallback
- State the deciding source when it materially influenced the implementation.

4. Surface newly explicit durable judgment when appropriate.
- If the repository conversation reveals a clearly reusable cross-repository principle and a local principle archive skill such as `$track-developer-principles` is available, surface the candidate after the implementation is stable. Update the archive only when the user explicitly requests or approves that write.
- Do not promote one-off local implementation details into archived principles.

5. Run the final gate before replying.
- If the repository provides an explicit autofix command, run it before the final gate so the last verification pass stays non-destructive.
- Review the actual diff for regressions, missing tests, architecture drift, HIG drift for UI-affecting changes, and Swift API/concurrency/package drift for Swift-affecting changes.
- Run the repository's documented verification contract, combining
  Xcode-native evidence and retained repository scripts when both are part of
  the contract.
- Treat current-change or clearly introduced build/test/lint/warning failures as blocking.
- If warnings or errors are clearly pre-existing or come from external packages, say so explicitly instead of attributing them to the current change.

6. Report clearly.
- Explain what changed, what decided the approach, what verification ran, and what remains unresolved.

## Guardrails

- Never start with a sibling reference repository.
- Never let archived principles override explicit user instructions or hard repository constraints.
- Never treat a generic sibling repository as stronger evidence than a relevant stored platform-foundation principle.
- Never treat an existing local UI pattern as decisive when it conflicts with current HIG or Apple official design guidance.
- Never treat an existing local Swift pattern as decisive when it conflicts with current Swift official guidance, API Design Guidelines, concurrency safety, or language semantics.
- Never treat a sibling repository as stronger evidence than a current relevant Apple sample project for framework adoption, app shell shape, or modern Apple-platform architecture.
- Never use non-Apple sources as the primary guidance when Apple official material is available.
- Never use non-Swift sources as the primary guidance when Swift official material is available.
- Never report success while current-change or clearly introduced verification issues remain unresolved.
- Never rely on `pre-commit` as the first place that auto-fixes SwiftLint issues; keep autofix in the main flow and leave the final gate non-destructive.
- Never rewrite repository artifacts into Japanese unless the task explicitly asks for that.

## Output Contract

Return concise Japanese with:

1. `変更内容`
2. `判断根拠`
3. `検証`
4. `保留事項`
