# Context Pack Format

Use this structure for archive-backed answers:

```markdown
**Context Pack**

**Scope**
- Archive root:
- Filters:
- Boundary note:

**Perspective / Evidence Mode**
- Evidence mode:
- Observer perspective:
- Absence rule:

**High-Confidence Evidence**
- Finding:
  Evidence: /path/to/raw/file.md
  Source id/date:

**Timeline**
- YYYY-MM-DD: event or decision
  Evidence: /path/to/raw/file.md

**People / Projects / Topics**
- People:
- Projects:
- Topics:

**Use Constraints / Staleness**
- Use policies:
- Derived record freshness:
- Rephrase or sharing constraints:

**Gaps**
- Missing or ambiguous evidence:
- Suggested next capture:

**Files Consulted**
- /path/to/raw/file.md
- /path/to/derived/file.md
```

Keep the pack evidence-first.
Do not bury uncertainty in the narrative.
Do not treat missing evidence as proof that something did not happen.
Keep non-archive memory separate from cited archive evidence unless the user explicitly requested memory-aware interpretation.
When evidence conflicts, show both cited records and describe the conflict without resolving it by guesswork.
