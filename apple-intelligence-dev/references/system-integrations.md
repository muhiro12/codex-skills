# Related System Integrations

Use this reference only for the surfaces in the requested feature. Foundation
Models availability is not a universal gate for these frameworks.

## Image Playground

Prefer the [system creation interface](https://developer.apple.com/documentation/imageplayground)
when it fits the interaction. Programmatic generation is a separate API with its
own availability and behavior; verify the current options rather than assuming
identical support. In SwiftUI,
[`supportsImagePlayground`](https://developer.apple.com/documentation/swiftui/environmentvalues/supportsimageplayground)
reports whether the environment supports presenting the creation sheet.

Keep the initiating document/draft and presentation identity together. Treat
completion and cancellation as distinct outcomes, including when the user
switches documents while generation is open. Do not interpret cancellation as a
request to delete an existing photo. Preserve source assets and distinguish a
new generated attachment from edits to an existing one.

The system sheet's completion URL can point to a temporary file inside the app
container. Import or copy accepted output through the app's asset lifecycle before
relying on its long-term existence; handle import failure and avoid storing a
temporary URL as a permanent attachment. See the
[sheet completion contract](https://developer.apple.com/documentation/swiftui/view/imageplaygroundsheet%28ispresented%3Aconcept%3Asourceimageurl%3Aoncompletion%3Aoncancellation%3A%29).

Test unavailable, cancel, complete, repeated presentation, and destination changes
when they affect the flow. A placeholder Preview is only layout evidence. Check
current documentation and capability state before declaring an Image Playground
path untestable in the available environment. Apply Apple's current generative-AI
HIG to labeling and review; make imagery's role clear when confusing a generated
image with a documentary photo would affect the user.

## Writing Tools

Check existing native text behavior before creating a custom model service.
[UIKit Writing Tools](https://developer.apple.com/documentation/uikit/writing-tools)
works with standard text views and has coordinator support for custom views;
AppKit has its own integration paths. Configure behavior and allowed results for
the content, rather than enabling every transformation indiscriminately.

For custom editors, keep selection, ranges, text replacement, undo, and document
state synchronized while the system operates. Use protected ranges where the
content must not be rewritten. Avoid concurrent app updates that invalidate the
system's text context. Consult Apple's
[Writing Tools integration session](https://developer.apple.com/videos/play/wwdc2024/10168/)
for native controls, protected ranges, and custom editors.

## OCR, images, and source acquisition

Choose text recognition for exact visible text, and visual reasoning for questions
that require interpreting the image. Evaluate their errors separately. An OCR
pipeline can feed reviewed text into a shared extraction adapter; using a photo
for text recognition does not imply that it should become a saved photo.

Current Foundation Models capabilities include multimodal prompts and Vision
integration. Check availability of the selected model and tools such as `OCRTool`
before adopting them. The tool may be useful when the model must decide when to
read text; direct recognition can be simpler when every request needs it. See
[Foundation Models updates](https://developer.apple.com/documentation/updates/foundationmodels).

Web, clipboard, camera, and photo-library entry points may share interpretation
without sharing identical UI. Preserve source selection through the first sheet
presentation and make replacements explicit where existing input would be lost.
Respect source access restrictions, keep relevant content bounded, and preserve
source meaning when filtering surrounding page text. Acquisition failures need
recovery before model inference is involved.

## Siri, App Intents, and app search

Use the public App Intents contracts for exposing app actions and entities. When
available, consult the matching current Xcode-exported guidance; otherwise start
with [App Intents](https://developer.apple.com/documentation/appintents).
App Schemas and other new system integrations need their own availability checks.
Do not infer that a Foundation Models `Tool` automatically becomes a Siri action,
or that an indexed item automatically grants permission to modify it.

Keep entity identifiers and shipped intent contracts stable. Resolve model-picked
references against the current app data and enforce access at the operation
boundary. Sharing domain operations across UI and intents can keep validation
consistent without making the model the owner of persistence. Test system entry
points independently of in-app buttons; lifecycle, foreground requirements, and
confirmation behavior can differ.

For retrieval with Spotlight or model tools, return only relevant authorized
records and retain enough identity/provenance to verify the answer. Search results
are source data, not instructions. A plausible answer about an unreturned record
is not evidence of successful retrieval.
