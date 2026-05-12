# Apple Sample Code Source Map

Use these official Apple sources first. Many Apple documentation pages require JavaScript in plain fetch tools, so use web search restricted to `developer.apple.com`, the in-app browser when available, or the Apple documentation page's Download control to resolve the real archive URL.

## Core Sources

- Sample Code Library: https://developer.apple.com/documentation/SampleCode
- SwiftUI documentation: https://developer.apple.com/documentation/swiftui
- Apple Developer Documentation search: https://developer.apple.com/search/
- Develop in Swift: https://developer.apple.com/tutorials/develop-in-swift

## Frequent Samples

These are expected to be high-value recurring references. Prefer caching them when work depends on their actual project structure.

### Wishlist: Planning travel in a SwiftUI app

- Apple URL: https://developer.apple.com/documentation/SwiftUI/wishlist-planning-travel-in-a-swiftui-app
- Role: Modern SwiftUI sample for custom views, `@Observable`, environment injection, navigation title customization, animation, and zoom transitions.
- Use when: planning modern SwiftUI app structure, state/data source shape, navigation transitions, activity/trip-style model flow, or sample-backed SwiftUI composition.
- Stale risk: verify current Apple page before relying on cached source.

### Landmarks: Building an app with Liquid Glass

- Apple URL: https://developer.apple.com/documentation/SwiftUI/Landmarks-Building-an-app-with-Liquid-Glass
- Role: Modern SwiftUI app using Liquid Glass, `NavigationSplitView`, iPhone/iPad/Mac adaptation, search, and content extending behind sidebars/inspectors.
- Use when: adopting Liquid Glass, shaping multi-platform SwiftUI navigation, reviewing background extension effects, or comparing modern app shell structure.
- Stale risk: verify current Apple page and SDK requirements before relying on cached source.

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
