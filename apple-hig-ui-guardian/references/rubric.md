# Apple HIG UI Rubric

Use this rubric for creation, audit, and repair. The goal is not to make every app look identical; it is to make the interface feel at home on Apple platforms, behave predictably, and remain accessible.

## Severity

- `blocking`: A core task is hard to complete, inaccessible, misleading, destructive without adequate confirmation, visually broken, or clearly against a major Apple platform convention.
- `warning`: The UI works but feels non-native, fragile, crowded, inconsistent, poorly adapted, or likely to fail under common settings such as Dynamic Type, dark mode, or iPad layout.
- `note`: A polish, documentation, coverage, or tradeoff observation that does not need to block the current change.

## Checks

### 1. Platform Fit

- Create: Choose the target platform and device idiom before layout details. Design for iPhone, iPad, macOS, watchOS, visionOS, widgets, and App Intents as different surfaces when applicable.
- Audit: Check whether the screen feels transplanted from another platform, ignores expected device ergonomics, or fails compact/regular width adaptation.
- Fix: Replace one-size-fits-all layouts with platform-adaptive containers, native navigation, and system affordances.

### 2. Navigation and Information Architecture

- Create: Use standard navigation structures such as `NavigationStack`, tab bars, sidebars, sheets, popovers, menus, and toolbars according to the task.
- Audit: Check whether people can tell where they are, what the primary task is, how to go back, and where destructive or modal actions will lead.
- Fix: Move primary destinations into expected containers and keep modal presentation for temporary, focused tasks.

### 3. Native Components and Controls

- Create: Prefer system controls and styles for buttons, toggles, pickers, sliders, forms, lists, search, menus, alerts, sheets, and toolbars.
- Audit: Treat custom controls as suspect when they duplicate native behavior without improving product meaning.
- Fix: Replace custom controls with native equivalents or make custom controls match native semantics, focus, accessibility, state, and interaction expectations.

### 4. Visual Hierarchy and Layout

- Create: Establish a clear hierarchy of content, primary actions, secondary actions, and supporting metadata. Respect safe areas, spacing, and platform-adaptive layout.
- Audit: Look for crowded surfaces, unclear primary actions, clipped text, overlapping controls, unsafe-area mistakes, inconsistent spacing, and poor iPad/macOS resizing.
- Fix: Simplify hierarchy, use semantic containers, improve spacing, and verify important states at multiple sizes.

### 5. Typography, Color, and Materials

- Create: Prefer system type styles, Dynamic Type, semantic colors, and system materials. Use custom visual language only where it strengthens the product and remains legible.
- Audit: Check text legibility, hierarchy, contrast, dark mode, color-only meaning, custom fonts, and overuse of decorative effects.
- Fix: Move raw colors and hard-coded text sizes toward semantic styles, scalable fonts, and contrast-aware variants.

### 6. Accessibility and Inclusive Interaction

- Create: Include accessibility labels, traits, values, hints when needed, sensible focus order, Dynamic Type support, sufficient hit targets, and alternatives to complex gestures.
- Audit: Check VoiceOver meaning, Voice Control labels, keyboard/pointer paths, gesture-only actions, text scaling, contrast, and whether controls are comfortable to tap or click.
- Fix: Add or repair semantic labels, roles, hit areas, gesture alternatives, scalable text, and color-independent indicators.

### 7. States, Feedback, and Safety

- Create: Design loading, empty, error, success, disabled, destructive, permission, and offline states with clear recovery paths.
- Audit: Look for hidden failures, unexplained spinners, unhelpful empty states, accidental destructive actions, and confirmation flows that block too much or too little.
- Fix: Add state-specific UI, progress or feedback, undo where appropriate, and clear destructive roles or confirmations.

### 8. Current Apple Visual Systems

- Create: Use current native APIs for visual systems such as Liquid Glass when the deployment target and product context fit.
- Audit: Check availability gates, fallbacks, material readability, interactive affordance, and whether effects obscure content or compete with hierarchy.
- Fix: Prefer native modifiers and system styles over custom blur, glass, shadow, or animation recreations.

### 9. Localization and System Terminology

- Create: Use localizable strings, platform terminology, official feature names, and layouts that tolerate longer localized text.
- Audit: Check hard-coded strings, unlocalized placeholders, unofficial translations of Apple feature names, clipped labels, and layout assumptions based on English or Japanese length.
- Fix: Move strings into the repository localization system and preserve official Apple terminology unless Apple provides a localized name.

## Review Questions

Ask these before concluding a UI is HIG-aligned:

- Does the screen's primary task read immediately from hierarchy and placement?
- Would a person familiar with this Apple platform know how to operate it without learning custom rules?
- Does it still work with larger text, dark mode, VoiceOver, keyboard or pointer input, and different device sizes?
- Are custom visuals or interactions carrying product meaning, or just replacing standard Apple behavior?
- Can every finding be tied to visible evidence, code evidence, or a specific Apple official source?
