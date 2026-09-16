# Related System Integrations

Foundation Models availability is not a universal gate for these frameworks.
Use each integration's documented capabilities and lifecycle.

## Image Playground

The [system creation interface](https://developer.apple.com/documentation/imageplayground)
and programmatic generation are distinct APIs; check availability and behavior
for the chosen path. In SwiftUI,
[`supportsImagePlayground`](https://developer.apple.com/documentation/swiftui/environmentvalues/supportsimageplayground)
reports support for presenting the creation sheet.

The [sheet completion contract](https://developer.apple.com/documentation/swiftui/view/imageplaygroundsheet%28ispresented%3Aconcept%3Asourceimageurl%3Aoncompletion%3Aoncancellation%3A%29)
returns an image at a temporary location inside the app container. Move accepted
output if it must survive sheet dismissal, and handle cancellation through its
separate callback. This API requirement does not specify the app's attachment
storage technology or whether images require a review screen.

Exercise completion, cancellation, repeated presentation, and changed destinations
when the app permits them. A placeholder Preview checks layout, not system image
generation. Use current capability evidence before declaring the feature
untestable. Consult Apple's [generative-AI HIG](https://developer.apple.com/design/human-interface-guidelines/generative-ai)
for the relevant presentation guidance.

## Writing Tools

[UIKit Writing Tools](https://developer.apple.com/documentation/uikit/writing-tools)
integrates with standard text views and provides a coordinator for custom views;
AppKit has its own integration. Check behavior and allowed result formats for the
editor in use. Custom editors need to keep text ranges, selection, replacement,
and undo consistent while system edits occur. Apple's
[Writing Tools session](https://developer.apple.com/videos/play/wwdc2024/10168/)
explains protected ranges and coordinator integration.

## OCR and image input

Text recognition and visual reasoning have different outputs and error modes.
Compare them for the required task. OCR can supply text to a Foundation Models
prompt; neither pipeline determines whether the app should retain the source
image or present intermediate text.

Current [Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels)
include multimodal prompts and Vision integration. Verify the selected model's
capabilities and APIs such as `OCRTool`. A model-selected OCR tool and direct
recognition are alternatives whose value depends on the task.

For web or OCR intake, inspect acquired content before diagnosing a model error.
If necessary facts never reached the prompt, changing generation options cannot
restore their source wording. See the source-omission
[development case](development-cases.md#source-omissions-and-rewritten-fields).

## Siri, App Intents, and app search

Use the relevant [App Intents](https://developer.apple.com/documentation/appintents)
contracts and current Xcode-exported guidance when available. A Foundation Models
`Tool` does not automatically become a Siri action; a new system integration has
its own availability, entity, and lifecycle requirements.

When supplying app-search results to a model, inspect retrieved identifiers and
content separately from the answer. Plausible prose does not demonstrate that
retrieval found the required record. Test system entry points separately when
their lifecycle or foreground requirements differ from the in-app path.
