# App Store "What's New" Template

Use this structure for App Store Connect:

## Metadata

- Version: `<version>`
- Release date: `<YYYY-MM-DD>`
- Commit range: `<from-ref>..<to-ref>`
- Source locale: `<source-locale>`
- Target locales: `<comma-separated locales>`

## Locale Text Template

`<locale>`

`<intro sentence>`

- `<User-visible change>`
- `<User-visible change>`
- `<User-visible change>`

`<optional closing sentence>`

## translations-json Shape

```json
{
  "ja": {
    "intro": "ExampleApp 5.5では、操作性と安定性を改善しました。",
    "items": [
      "通知やウィジェットなどから、目的の画面へよりスムーズに移動できるようになりました。",
      "月・予定・純収支ウィジェットの表示バランスとレイアウトを調整しました。",
      "そのほか、軽微な不具合修正と細かな改善を行いました。"
    ],
    "outro": "日々の入力がさらにスムーズになるアップデートです。"
  }
}
```
