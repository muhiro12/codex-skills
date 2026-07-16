# Apple Sample Code Source Map

Use these official Apple sources first. Many Apple documentation pages require JavaScript in plain fetch tools, so use web search restricted to `developer.apple.com`, the in-app browser when available, or the Apple documentation page's Download control to resolve the real archive URL.

## Core Sources

- Sample Code Library: https://developer.apple.com/documentation/SampleCode
- SwiftUI documentation: https://developer.apple.com/documentation/swiftui
- Apple Developer Documentation search: https://developer.apple.com/search/
- Develop in Swift: https://developer.apple.com/tutorials/develop-in-swift

## Preferred Reference Samples

These are intentionally curated samples to consider early when they are relevant to a task. This list expresses a maintained reference preference; it is not derived from observed usage frequency. Prefer using their actual project structure when it can materially clarify an implementation or architecture decision.

### Wishlist: Planning travel in a SwiftUI app

- Apple URL: https://developer.apple.com/documentation/SwiftUI/wishlist-planning-travel-in-a-swiftui-app
- Role: Modern SwiftUI sample for custom views, `@Observable`, environment injection, navigation title customization, animation, and zoom transitions.
- Use when: planning modern SwiftUI app structure, state/data source shape, navigation transitions, activity/trip-style model flow, or sample-backed SwiftUI composition.
- Stale risk: verify current Apple page before relying on cached source.

### Origami: Crafting a dynamic tutorial for Apple Intelligence

- Apple URL: https://developer.apple.com/documentation/FoundationModels/origami-crafting-a-dynamic-tutorial-for-apple-intelligence
- Role: Modern Foundation Models sample for multimodal prompting, guided generation, tool calling, shared-session orchestration, and Private Cloud Compute.
- Use when: designing multi-step intelligent features, coordinating model-driven app states, analyzing user-provided images, generating structured tutorials, or separating model instructions, tools, and UI state.
- Stale risk: verify the current Apple page, model availability, and SDK requirements before relying on cached source.

## Search Patterns

- `site:developer.apple.com/documentation sample code <framework> <feature>`
- `site:developer.apple.com/documentation/SwiftUI <sample title> Download`
- `site:developer.apple.com/documentation/SampleCode <framework> <topic>`
- `site:developer.apple.com/documentation <sample title> View sample code`
- `site:developer.apple.com/documentation <WWDC year> <framework> sample code`

## Download Resolution Notes

- Apple sample pages often expose a `Download` control only in the rendered documentation UI.
- If plain web fetch shows only a JavaScript placeholder, use search snippets, the in-app browser, or browser automation to locate the real download URL.
- When a real archive URL is found, use `scripts/sample_cache.py fetch-archive`.
- If the archive was downloaded manually, use `scripts/sample_cache.py add-local`.
- Record the original Apple documentation URL even when the source archive URL is different.
