---
name: apple-ios-dev-flow
description: Orchestrate Apple-platform app development in this local Codex/Xcode environment by routing implementation, refactor, UI, Swift, sample-code, simulator, App Intents, performance, leak, preview, smoke, and verification work across Hiromu's custom skills, OpenAI Build iOS Apps skills, XcodeBuildMCP, Apple official guidance, repo-local evidence, and the repository's standard verification shell.
---

# Apple iOS Dev Flow

## Overview

Use this skill as the default entrypoint and orchestrator for ordinary Apple-platform implementation requests in this PC environment.
Keep the workflow core in this file portable across agent runtimes where practical; platform-specific metadata can live beside the skill.
Return user-facing explanations in concise, practical Japanese.
Keep code, commands, file names, identifiers, and repository documents in English unless the target repository already uses another convention.
Treat this skill as the place that chooses evidence, gates, and specialist skills. Do not duplicate the detailed implementation procedures from sidecar skills; route to them when their trigger is a better fit.
When implementation depends on recurring cross-repository judgment, consult a local principle archive skill when available (for example `$track-developer-principles`) before settling the approach.
When implementation affects user interface, navigation, controls, visual hierarchy, accessibility, platform adaptation, or Apple design-system behavior, use `$apple-hig-ui-guardian` before settling or preserving the UI shape.
When implementation affects Swift APIs, naming, type modeling, concurrency, `Sendable`, actor isolation, package/module boundaries, access control, public documentation, or SwiftPM manifests, use `$swift-code-guardian` before settling or preserving the code shape.
When implementation depends on project-level Apple architecture, framework adoption, app shell shape, target layout, lifecycle wiring, entitlements, or modern sample-backed patterns, use `$apple-sample-code-advisor` before falling back to sibling repositories.
When available and relevant, use OpenAI Build iOS Apps skills and XcodeBuildMCP for specialized SwiftUI, App Intents, simulator, profiling, and leak workflows, while still treating the repository's standard shell as the final verification gate.

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

- Hiromu custom skills: `$track-developer-principles`, `$apple-hig-ui-guardian`, `$swift-code-guardian`, `$apple-sample-code-advisor`, `$xcode-preview-auditor`, `$xcode-ui-smoke-auditor`, `$ci-verify-and-summarize`, and repository workflow skills.
- OpenAI Build iOS Apps skills: `$build-ios-apps:swiftui-ui-patterns`, `$build-ios-apps:swiftui-view-refactor`, `$build-ios-apps:swiftui-liquid-glass`, `$build-ios-apps:swiftui-performance-audit`, `$build-ios-apps:ios-app-intents`, `$build-ios-apps:ios-debugger-agent`, `$build-ios-apps:ios-ettrace-performance`, and `$build-ios-apps:ios-memgraph-leaks`.
- Local Apple sample cache: `~/.codex/cache/apple-sample-code`, managed through `$apple-sample-code-advisor`.
- XcodeBuildMCP for simulator build, run, logs, UI inspection, screenshots, and profiling support when available.
- Repository standard shells, especially `AGENTS.md` and `ci_scripts/tasks/verify.sh` style entrypoints.
- Local sibling repositories only as read-only fallback evidence after stronger Apple and current-repo sources.

## Decision Order

1. Start from current repository evidence.
- Read the affected code, tests, diagnostics, `AGENTS.md`, and `ci_scripts` first.
- Preserve the repository's better Apple-appropriate pattern when it is already clear.

2. Use a local principle archive skill second when judgment matters.
- Consult it when the task depends on tradeoffs such as maintainability, architecture direction, product intent, workflow philosophy, naming heuristics, or quality bars that may repeat across repositories.
- If stored principles point to a maintained platform foundation such as `../MHPlatform` for shared stack, reusable plumbing, or cross-app implementation direction, treat that as part of the current decision context before falling back to a generic sibling reference repository.
- Treat explicit current-task instructions and hard repository constraints as higher priority than older archived principles when they conflict.

3. Apply the HIG gate for UI-affecting work.
- For changes that affect user-visible Apple UI, invoke `$apple-hig-ui-guardian` and read its rubric before editing or approving the UI shape.
- Treat HIG and current Apple official design guidance as active constraints, not only as fallback references when the implementation is unclear.
- Preserve local UI conventions only when they remain compatible with HIG; name intentional product-driven departures from HIG.

4. Apply the Swift code gate for Swift-language work.
- For changes that affect Swift APIs, package boundaries, concurrency, type modeling, documentation, or public/reusable code, invoke `$swift-code-guardian` and read its rubric before editing or approving the code shape.
- Treat official Swift documentation, API Design Guidelines, and concurrency guidance as active constraints, not only as fallback references when the implementation is unclear.
- Preserve local Swift style only when it remains compatible with Swift clarity, safety, and language semantics.

5. Use Apple, Swift, and sample-code official guidance next.
- When the implementation shape is still unclear, prefer Apple documentation, Swift.org documentation, Human Interface Guidelines, WWDC material, Swift API Design Guidelines, Swift language guidance, and Apple sample code.
- Prefer Apple or Swift official guidance over general web advice.

6. Use Apple sample projects before sibling repositories when project-level shape matters.
- For framework adoption, app architecture, lifecycle, target boundaries, or cross-surface implementation patterns, invoke `$apple-sample-code-advisor` and inspect cached or current Apple sample projects before using a sibling repository as evidence.
- Treat sample code as official implementation evidence, but still subordinate to product constraints, HIG, Swift language guidance, and framework API documentation.

7. Route execution to OpenAI Build iOS Apps specialist skills when they match the task.
- Use specialist skills for concrete SwiftUI, App Intents, simulator, performance, ETTrace, or leak workflows after the current-repo and official-guidance gates establish the intended direction.
- Treat specialist workflow guidance as implementation help; do not let it override explicit product constraints, HIG, Swift language guidance, framework documentation, or current Apple sample evidence.

8. Use a locally available sibling reference repository last as a read-only fallback.
- If a locally available sibling reference repository is available and relevant, inspect it only after current-repo evidence plus Apple, Swift, and sample-code official guidance still do not settle the approach.
- Borrow reusable workflow or architecture intent, not app-specific UX, domain models, or naming.

## Specialist Routing

Use this routing before editing when a sidecar skill can narrow the work:

- General SwiftUI screen or component creation: use `$apple-hig-ui-guardian`, then `$build-ios-apps:swiftui-ui-patterns`; add `$swift-code-guardian` when API shape or state modeling matters.
- SwiftUI view cleanup or body decomposition: use `$build-ios-apps:swiftui-view-refactor`, plus `$swift-code-guardian` for Observation, dependency injection, access control, and concurrency boundaries.
- Liquid Glass work: use `$apple-hig-ui-guardian`, `$build-ios-apps:swiftui-liquid-glass`, and `$apple-sample-code-advisor` for current Landmarks-style sample evidence when project-level shape matters.
- App Intents, App Entities, App Shortcuts, Siri, Spotlight, widgets, or controls integration: use `$build-ios-apps:ios-app-intents`, plus `$swift-code-guardian` for API and concurrency quality.
- Simulator run, UI interaction, runtime logs, screenshots, or live debugging: use `$build-ios-apps:ios-debugger-agent` and XcodeBuildMCP; call the XcodeBuildMCP session-default discovery step before the first build/run/test call in a session.
- SwiftUI performance diagnosis from code: use `$build-ios-apps:swiftui-performance-audit`; use `$build-ios-apps:ios-ettrace-performance` when runtime trace evidence is required.
- Memory growth, retain cycles, or leak proof: use `$build-ios-apps:ios-memgraph-leaks`, usually paired with `$build-ios-apps:ios-debugger-agent` for the live simulator flow.
- Preview-based visual audit: use `$xcode-preview-auditor`, then `$apple-hig-ui-guardian` for HIG classification of any issues.
- Live release UI smoke or screenshot audit: use `$xcode-ui-smoke-auditor`, then `$apple-hig-ui-guardian` for UI/design-system findings.
- Project-level architecture, framework adoption, lifecycle, target layout, entitlements, or modern app shell decisions: use `$apple-sample-code-advisor` before sibling repository fallback.
- Final verification and diff summary: use `$ci-verify-and-summarize` when the user asks for verify/CI/push-readiness summarization; otherwise run the repository's standard verification shell directly.

## Workflow

1. Confirm repository workflow prerequisites.
- Resolve the repository's standard verification entrypoint from `AGENTS.md` first, then `ci_scripts/**/*.sh`, then repo-native aggregate commands.
- If the repository provides an explicit repo-managed autofix step for edited files such as `format_swift.sh`, treat it as part of the main implementation flow before the final verification gate.
- If the repository does not have a coherent standard shell for build/test/lint verification, switch to `$apple-repo-verify-bootstrapper` or tell the user that the repo needs that scaffolding first.
- For simulator execution or UI/debug validation, prefer XcodeBuildMCP tools when available; call `session_show_defaults` before the first XcodeBuildMCP build/run/test call in a session, and use the repo-standard shell afterward for final readiness.

2. Implement with local evidence first.
- Inspect the target files, adjacent tests, and current diagnostics before editing.
- Keep the patch as small and local as the task allows.
- For UI-affecting changes, use `$apple-hig-ui-guardian` to choose or review the UI approach before preserving local visual patterns.
- For Swift-affecting changes, use `$swift-code-guardian` to choose or review API shape, type modeling, concurrency, documentation, package, and access-control decisions before preserving local code patterns.
- For framework adoption, app shell, lifecycle, target-boundary, or cross-surface architecture decisions, use `$apple-sample-code-advisor` before borrowing from a sibling repository.

3. Make implementation decisions in this order.
- current repository evidence
- a local principle archive skill when available and the decision is judgment-heavy
- `$apple-hig-ui-guardian` for UI-affecting work
- `$swift-code-guardian` for Swift-language, API, concurrency, or package-boundary work
- Apple official guidance
- Swift official guidance
- `$apple-sample-code-advisor` for official project-level sample evidence
- OpenAI Build iOS Apps specialist skills for task-specific implementation workflow
- a locally available sibling reference repository read-only fallback
- State the deciding source when it materially influenced the implementation.

4. Harvest newly explicit durable judgment when appropriate.
- If the repository conversation reveals a clearly reusable cross-repository principle and a local principle archive skill such as `$track-developer-principles` is available, update it after the implementation is stable.
- Do not promote one-off local implementation details into archived principles.

5. Run the final gate before replying.
- If the repository provides an explicit autofix command, run it before the final gate so the last verification pass stays non-destructive.
- Review the actual diff for regressions, missing tests, architecture drift, HIG drift for UI-affecting changes, and Swift API/concurrency/package drift for Swift-affecting changes.
- Run the repository's standard verification entrypoint.
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
