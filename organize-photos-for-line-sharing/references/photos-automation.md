# Photos automation reference

Read this file before composing AppleScript or mutating a Photos album.

## Safety boundary

- Address media by Photos `id`, never by filename alone.
- Use Photos only through supported UI or scripting surfaces.
- Never write inside `Photos Library.photoslibrary` or another `.photoslibrary` bundle.
- Never issue `delete` against a media item.
- Do not assume `delete media items of album` means remove only from the album; it can threaten the library.
- Prefer create, add, verify, and rename. Retain the original album as a backup.
- Exporting creates copies. Never re-import review copies, and never delete them without explicit approval.

## Observed scripting surface

The Photos AppleScript dictionary exposes writable `date` on a media item and read-only `id`, `filename`, `width`, and `height`. It supports creating albums and adding media items to an album. It does not expose image rotation or a clearly safe remove-from-album command.

Treat these observations as version-sensitive. Reinspect the active Photos scripting dictionary after a major macOS update.

## Reliable reads

Read bulk properties directly from `every media item`:

```applescript
tell application "Photos"
    set itemDates to date of every media item
    set itemFilenames to filename of every media item
    set itemIDs to id of every media item
    set itemWidths to width of every media item
    set itemHeights to height of every media item
end tell
```

Do not first assign `every media item` to a variable and then ask for `date of thatVariable`; Photos can fail with `-1728`.

Do not rely on `whose date ...` predicates. Retrieve values and filter them locally. Ensure parallel property arrays have equal lengths before correlating by index. If lengths differ, fall back to per-item reads or smaller batches.

When returning an ID list, join with linefeeds:

```applescript
tell application "Photos"
    set itemIDs to id of every media item of album "203001"
    set oldDelimiters to AppleScript's text item delimiters
    set AppleScript's text item delimiters to linefeed
    set outputText to itemIDs as text
    set AppleScript's text item delimiters to oldDelimiters
    return outputText
end tell
```

Photos search includes visual and OCR results. A search for `LINE` is not reliable source attribution. Prefer filenames, IDs, date clusters, and visual review.

## Resolve media IDs

Resolve IDs inside Photos and add them as a list:

```applescript
tell application "Photos"
    set targetAlbum to album "__TEMP_203001__"
    set targetIDs to {"MEDIA-ID-1", "MEDIA-ID-2"}
    set targetItems to {}
    repeat with targetID in targetIDs
        set end of targetItems to media item id (contents of targetID)
    end repeat
    add targetItems to targetAlbum
end tell
```

Use batches of at most 50. For a new album, start with a smaller batch such as 20 if Photos stalls. Wrap long operations in `with timeout of 600 seconds` and poll a yielded command rather than launching a competing write.

Adding an item already present in an album is idempotent in the observed Photos version, but still verify unique IDs after every batch.

## Export review copies

Create a unique task directory first. Export only the IDs needed for visual review:

```applescript
with timeout of 600 seconds
    tell application "Photos"
        set targetItems to {media item id "MEDIA-ID-1"}
        export targetItems to POSIX file "/private/tmp/task-specific-dir" using originals true
    end tell
end timeout
```

Use the bundled contact-sheet script on the exported copies. Keep the Photos library untouched.

## Date correction

Photos UI date adjustment displays minute precision while the underlying seconds can remain. AppleScript can write a complete `date` value. Before a write:

1. Store media ID, original timestamp, proposed timestamp, and evidence.
2. Verify the proposed order against adjacent confirmed LINE items.
3. Apply only confirmed changes.
4. Read back each exact timestamp.

For the established 23:50 policy, preserve the original minute ones digit and seconds where possible. For example, `14:27:43` becomes `23:57:43` on the inferred date. This modifies the date, hour, and minute tens digit while retaining finer ordering. Do not force every item to the same timestamp.

## Safe album replacement

For each changed month:

1. Ensure neither the temporary album nor backup name conflicts with an unrelated album.
2. Create `__TEMP_NO_LINE_YYYYMM__`.
3. Add only the expected outbound media IDs.
4. Read the album IDs and compare sets locally.
5. Require missing `0`, extra `0`, duplicates `0`, confirmed LINE `0`, and unresolved LINE candidates `0`.
6. Rename `YYYYMM` to `YYYYMM_LINE_INCLUDED_BACKUP_YYYYMMDD`.
7. Rename the temporary album to `YYYYMM`.
8. Verify both the new album and retained backup.

Example rename pattern with synthetic album names:

```applescript
tell application "Photos"
    if exists album "203001_LINE_INCLUDED_BACKUP_20300201" then error "backup exists"
    set name of album "203001" to "203001_LINE_INCLUDED_BACKUP_20300201"
    set name of album "__TEMP_NO_LINE_203001__" to "203001"
end tell
```

Do not perform all months in a single irreversible chain without verifying each temporary album first. If a rename fails midway, stop; the media remain safe and both albums can be identified by name.

## Computer Use verification

After every UI action, refresh the Photos state through the active Computer Use tool. Resolve its current actions from the available tool instructions and re-derive element indexes from the current accessibility tree.

Use these accessibility values as evidence:

- `FooterTitle`: photo and video totals.
- `FooterSubtitle`: iCloud sync status.
- Album text fields: exact album names.
- Visible media descriptions: dates and display orientation.

Accessibility `Help: 90度回転` is not proof that the displayed image is wrong. Judge actual content from a screenshot or exported copy.

## Failure recovery

- AppleEvent timeout while adding to a new album: query its count, then retry a smaller batch. Do not assume partial success or failure.
- Backup already exists: stop and inspect. Never overwrite it automatically.
- Library count increased: inspect the newly arrived last items individually and classify them before adding them to a month.
- Library count decreased: stop all writes and report the discrepancy immediately.
- Expected-set mismatch: keep the temporary and original albums unchanged by name until the mismatch is explained.
- Active iCloud sync: wait when practical, then run the full final verification again.
