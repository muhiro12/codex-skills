---
name: organize-photos-for-line-sharing
description: Safely organize Apple Photos for outbound LINE sharing by inventorying a date range, distinguishing self-captured originals from inbound LINE downloads, preserving trusted dates on originals, normalizing only confirmed LINE dates, actively correcting orientation on originals, conservatively rotating LINE media, building monthly albums from outbound originals only, verifying zero deletion, and producing a visual HTML report. Use for recurring macOS Photos cleanup, YYYYMM album creation, LINE-download separation, 23:50 date normalization, source-aware orientation correction, or correction of previously mixed monthly albums.
---

# Organize Photos for LINE Sharing

Treat the Photos library as the irreplaceable source. Build outbound sharing albums; do not treat inbound LINE downloads as photos to send back.

## Non-negotiable contract

- Never delete a photo or video. Never invoke Photos `delete` on a media item, Recently Deleted, direct Photos-library database writes, or filesystem mutation inside a `.photoslibrary` bundle.
- Never use a removal operation whose effect on the library is uncertain. Rebuild an album and retain its old version under a backup name instead.
- Never change a date from filename, dimensions, or a search result alone. Use dimensions only to find orientation candidates, then judge visible content before rotating.
- Never change the date of a self-captured or otherwise trusted non-LINE original. Date correction is exclusively for confirmed LINE downloads.
- Never apply the landscape preference for self-captured originals to confirmed LINE downloads. Rotate LINE media only when visible content is clearly sideways.
- Never change the date or orientation of an item whose source classification is unresolved.
- Never delete exported review copies unless the user explicitly approves deleting those exact temporary copies.
- Stop immediately if the library media count decreases. Investigate before any further mutation.
- For audit, explanation, or feasibility requests, remain read-only.

## Establish the contract

Confirm or infer only when unambiguous:

1. Set the inclusive date range and monthly album naming convention, normally `YYYYMM`.
2. Determine whether albums contain still images only. Default to still images when the user says photos or images; report excluded videos.
3. Record that the album purpose is outbound LINE sharing. Classify each item before mutation as `outbound_original`, `confirmed_line`, or `unresolved_or_other`. Only `outbound_original` items belong in the monthly albums.
4. Record the requested date policy. Treat dates on `outbound_original` items as trusted and immutable. For `confirmed_line` items only, prefer an exact day, fall back to the month's last day, place them in the 23:50 band, and preserve source order.
5. Record the source-aware rotation policy. Actively review `outbound_original` portrait images with landscape as the default intent. Review `confirmed_line` orientation conservatively without a landscape preference.
6. Leave `unresolved_or_other` items out of the albums and make no date or orientation change until their source and purpose are resolved.
7. Use a deterministic backup suffix such as `_LINE_INCLUDED_BACKUP_YYYYMMDD`. Never overwrite an existing backup.

Ask before mutation when any item above would materially change the result.

## Use the supported surfaces

- Read the active Computer Use tool instructions before inspecting or operating the Photos UI; use a matching installed skill when available.
- Prefer Photos AppleScript for read-only metadata, album creation, album addition, and album renaming when the user permits programmatic work.
- Use the Photos UI for visual judgment and rotation because Photos AppleScript does not expose rotation.
- Read [references/photos-automation.md](references/photos-automation.md) before composing Photos AppleScript or changing an album.

## Workflow

### 1. Capture a preflight snapshot

1. Read the Photos footer totals and iCloud sync status through Computer Use.
2. Record `count of every media item` through Photos AppleScript.
3. Record exact names, counts, and media IDs for target monthly albums and any pre-existing backup albums.
4. Wait for active synchronization to settle when practical. Treat count increases during the task as possible new iCloud arrivals, never as automatic evidence of an error.
5. Create a task-specific temporary directory with `mktemp -d`. If retaining artifacts under this skill, use its Git-ignored `work/` directory. Keep inventories, media IDs, exports, contact sheets, and run reports out of version control. Do not target a broad directory for cleanup.

### 2. Inventory without mutation

Export these tab-separated fields for each item: year, month, day, hour, minute, second, filename, Photos media ID, width, and height. Filter the requested date range outside Photos; Photos date predicates can be unreliable.

Run the deterministic analyzer first with UUID names treated as candidates:

The examples use `work/`; create it before use or substitute the task-specific temporary directory.

```bash
python3 scripts/analyze_inventory.py work/inventory.tsv \
  --start-year 2026 \
  --uuid-policy candidate \
  --output work/plan.json
```

Use filename evidence as follows:

- Treat an explicit `LINE_` prefix as strong LINE-download evidence.
- Treat a UUID-style filename as a candidate, not proof. Inspect representative originals or contact sheets and correlate date clusters, source order, file type, and nearby non-LINE originals.
- UUID-style names and a 23:50 timestamp cluster are not specific to LINE. Confirm the source convention for the current library from independent visual and contextual evidence on every run.
- Keep generated assets, screenshots, and other downloads separate when visual evidence shows they are not from LINE.
- Exclude unresolved possible LINE downloads from outbound sharing albums while leaving them untouched in the library.
- Treat the analyzer's non-LINE `outbound` IDs as candidates until visual and contextual evidence confirms that they are self-captured originals intended for sharing. Do not add generated assets, unrelated downloads, or unresolved sources merely because they are not LINE files.

After validating the convention, rerun with `--uuid-policy line`, or pass reviewed IDs through `--line-id-file`. Preserve the resulting JSON manifest as the dry-run evidence.

### 3. Review dates and sequence for confirmed LINE downloads only

Only plan a date write for confirmed LINE downloads.

1. First require that every proposed date-change ID is present in the confirmed LINE set and absent from the outbound-original set. A proposed date change for an outbound original is a blocking error.
2. Infer the target day from visually similar, correctly dated non-LINE photos and surrounding sequences without modifying those reference photos.
3. If only the month is defensible, use that month's final calendar day.
4. Preserve the original minute ones digit and seconds where that maintains order: set the hour to `23` and replace only the minute tens digit with `5`.
5. Verify that the proposed timestamps remain strictly nondecreasing in the confirmed source order. Resolve collisions with the smallest permitted adjustment; otherwise skip the ambiguous item.
6. Produce a before/after manifest before applying any date change. Explicitly record `non_line_date_changes: 0`.
7. Re-read every changed date after applying it. Do not infer success from the dialog closing.

LINE date correction is independent from outbound album assignment. A corrected LINE date must never determine an outbound album destination; album assignment uses only the unchanged capture dates of confirmed outbound originals.

### 4. Review orientation according to source

Export review copies, never originals out of the library, into the task-specific temporary directory. Generate contact sheets with:

```bash
swift scripts/make_photo_contact_sheets.swift work/exported-images work/contact-sheets
```

#### Self-captured outbound originals: active correction

Inspect every self-captured still image in scope whose displayed dimensions are portrait, plus any landscape-dimension image whose content appears sideways. Treat portrait dimensions as a review trigger and landscape as the user's normal intended result, not as sufficient evidence for a blind rotation.

Classify each portrait candidate:

- `rotate`: one 90-degree direction makes people, horizons, architecture, or text naturally upright and yields the intended composition. Choose clockwise or counterclockwise from visible content. For portrait-aspect originals, prefer the credible landscape result.
- `keep_portrait`: positive visual evidence shows intentional portrait composition, such as a deliberate full-height subject, vertical artwork, or a sequence consistently framed upright.
- `unresolved`: neither direction is defensible. Leave it unchanged, but report it prominently for manual review.

Do not preserve portrait merely because the content is currently upright; require positive evidence that the composition is intended to remain vertical. Do not rotate merely because Photos accessibility text says `90度回転`; that can describe valid metadata orientation.

#### Confirmed LINE downloads: conservative correction

Do not use portrait dimensions alone as a review trigger or assume that landscape was intended. The sender may have deliberately created a portrait photo, screenshot, document, illustration, or graphic.

- Review a confirmed LINE item for rotation only when visible content or its surrounding sequence gives concrete evidence that it is sideways.
- Rotate only when one 90-degree direction clearly restores the intended upright view. Do not rotate merely to make the result landscape.
- If the current orientation is plausible or the direction is uncertain, leave it unchanged.

Do not rotate `unresolved_or_other` items. After any rotation, refresh the Photos UI and verify that the displayed result is visibly upright before continuing. Record the source class, media ID, original dimensions, chosen direction, final dimensions, and decision evidence. Count self-captured and LINE rotation decisions separately.

### 5. Build outbound monthly albums

Compute each album's expected set as:

`confirmed self-captured outbound originals in their unchanged capture-date month`

Confirmed LINE downloads, unresolved LINE candidates, generated assets, other downloads, and unresolved sources remain outside the outbound albums. LINE date correction must never cause an item to enter an outbound album.

Then apply conservatively:

1. Leave an existing monthly album unchanged when its exact ID set already matches.
2. For a changed month, create a uniquely named temporary album.
3. Add expected media IDs in batches of at most 50. Newly created albums may need a small first batch before larger additions.
4. Verify exact ID equality: expected count, actual count, missing `0`, extra `0`, duplicate `0`, confirmed LINE `0`, unresolved LINE candidate `0`.
5. Abort if the intended backup name already exists.
6. Rename the old album to `YYYYMM_LINE_INCLUDED_BACKUP_YYYYMMDD`.
7. Rename the verified temporary album to the original `YYYYMM` name.
8. Retain the backup. Do not delete it as part of this skill unless the user separately and explicitly asks to remove only the album container.

Do not rebuild unaffected months merely for consistency.

### 6. Reconcile synchronization and verify

1. Re-read the library total and Photos footer after album changes.
2. If the library count increased, identify the new items individually. Add only newly confirmed self-captured originals to the applicable outbound month, using their existing capture dates.
3. If the library count decreased, stop and investigate immediately.
4. Re-read every requested monthly album ID set.
5. Require missing `0`, extra `0`, duplicate `0`, confirmed LINE `0`, and unresolved LINE candidate `0` for every outbound album.
6. Confirm that no media date or rotation changed beyond the approved, source-classified manifest. Require zero date changes for non-LINE originals.
7. Confirm the final Photos sync status through Computer Use.

## Generate the visual HTML report

Generate a visual HTML report after every completed run, including read-only or no-change runs. If the run is blocked after collecting evidence, generate a blocked report instead of omitting the report.

1. Create `run-report.json` following [references/report-schema.md](references/report-schema.md).
2. Keep the report outside every `.photoslibrary` bundle. Use a user-requested output directory, a task artifact directory, or a task-specific temporary directory.
3. Generate the self-contained report:

```bash
python3 scripts/generate_html_report.py work/run-report.json work/photos-line-sharing-report.html
```

4. Render or open the HTML at a normal desktop width and a narrow width. Fix clipped labels, unreadable bars, missing sections, or unescaped content.
5. Present the HTML report to the user and retain the JSON beside it so a future run can compare results.

The report must make these values visually scannable:

- final count for each monthly album;
- confirmed LINE downloads excluded by month and in total;
- unresolved candidates omitted from sharing albums;
- self-captured portrait candidates, active rotations, clearly retained portrait images, and unresolved orientation items;
- confirmed LINE items reviewed conservatively, rotations of clearly sideways LINE media, unchanged LINE items, and unresolved LINE orientation items;
- confirmed LINE date corrections and an explicit non-LINE date-change count of zero;
- total rotations, split between self-captured originals and confirmed LINE downloads;
- missing, extra, and duplicate verification results;
- library count before and after, explaining any synchronized arrivals;
- backup album names;
- the explicit statement `写真・動画の削除: 0件`.

Never claim the library count was unchanged when iCloud synchronization added media during the task.

## Resources

- Use [scripts/analyze_inventory.py](scripts/analyze_inventory.py) for deterministic candidate classification and monthly-set planning. It never writes to Photos.
- Use [scripts/make_photo_contact_sheets.swift](scripts/make_photo_contact_sheets.swift) to create review sheets from exported copies. It never modifies input images.
- Use [scripts/generate_html_report.py](scripts/generate_html_report.py) to create the required self-contained post-run report.
- Use [references/photos-automation.md](references/photos-automation.md) for Photos scripting patterns, API limitations, and failure recovery.
- Use [references/report-schema.md](references/report-schema.md) when assembling the post-run report manifest.
