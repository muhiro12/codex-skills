#!/usr/bin/env python3
"""Build a read-only monthly Photos plan from a TSV inventory."""

from __future__ import annotations

import argparse
import calendar
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Tuple


UUID_NAME = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[^.]+$",
    re.IGNORECASE,
)
IMAGE_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".dng",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".png",
    ".raw",
    ".tif",
    ".tiff",
    ".webp",
}
VIDEO_EXTENSIONS = {".m4v", ".mov", ".mp4"}


@dataclass(frozen=True)
class Media:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    filename: str
    media_id: str
    width: int
    height: int

    @property
    def timestamp(self) -> datetime:
        return datetime(
            self.year,
            self.month,
            self.day,
            self.hour,
            self.minute,
            self.second,
        )

    @property
    def extension(self) -> str:
        return Path(self.filename).suffix.lower()

    @property
    def kind(self) -> str:
        if self.extension in VIDEO_EXTENSIONS:
            return "video"
        if self.extension in IMAGE_EXTENSIONS:
            return "image"
        return "other"

    @property
    def is_explicit_line(self) -> bool:
        return self.filename.upper().startswith("LINE_")

    @property
    def is_uuid_name(self) -> bool:
        return UUID_NAME.fullmatch(self.filename) is not None

    @property
    def in_2350_band(self) -> bool:
        return self.hour == 23 and 50 <= self.minute <= 59


def positive_year(value: str) -> int:
    year = int(value)
    if year < 1:
        raise argparse.ArgumentTypeError("year must be positive")
    return year


def parse_month(value: str) -> tuple[int, int]:
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError as error:
        raise argparse.ArgumentTypeError("month must use YYYY-MM") from error
    return parsed.year, parsed.month


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a Photos TSV inventory without mutating Photos."
    )
    parser.add_argument("inventory", type=Path, help="TSV inventory path")
    parser.add_argument("--start-year", type=positive_year, required=True)
    parser.add_argument(
        "--through",
        type=parse_month,
        metavar="YYYY-MM",
        help="inclusive final month; defaults to all inventory months",
    )
    parser.add_argument(
        "--uuid-policy",
        choices=("candidate", "line", "ignore"),
        default="candidate",
        help="classification for UUID-style filenames",
    )
    parser.add_argument(
        "--line-id-file",
        type=Path,
        help="optional newline-delimited media IDs confirmed as LINE downloads",
    )
    parser.add_argument("--summary-only", action="store_true")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    return parser.parse_args()


def read_inventory(path: Path) -> list[Media]:
    records: list[Media] = []
    seen_ids: set[str] = set()

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\n")
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) != 10:
                raise ValueError(
                    f"{path}:{line_number}: expected 10 TSV fields, found {len(fields)}"
                )
            try:
                record = Media(
                    year=int(fields[0]),
                    month=int(fields[1]),
                    day=int(fields[2]),
                    hour=int(fields[3]),
                    minute=int(fields[4]),
                    second=int(fields[5]),
                    filename=fields[6],
                    media_id=fields[7],
                    width=int(fields[8]),
                    height=int(fields[9]),
                )
                record.timestamp
            except ValueError as error:
                raise ValueError(f"{path}:{line_number}: invalid field: {error}") from error
            if not record.filename or not record.media_id:
                raise ValueError(f"{path}:{line_number}: filename and ID are required")
            if record.media_id in seen_ids:
                raise ValueError(f"{path}:{line_number}: duplicate ID {record.media_id}")
            seen_ids.add(record.media_id)
            records.append(record)

    return records


def read_confirmed_ids(path: Optional[Path]) -> set[str]:
    if path is None:
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def within_scope(
    record: Media, start_year: int, through: Optional[Tuple[int, int]]
) -> bool:
    if record.year < start_year:
        return False
    if through is None:
        return True
    return (record.year, record.month) <= through


def ids(records: Iterable[Media]) -> list[str]:
    return [record.media_id for record in records]


def build_plan(args: argparse.Namespace) -> dict[str, object]:
    all_records = read_inventory(args.inventory)
    reviewed_line_ids = read_confirmed_ids(args.line_id_file)
    known_ids = {record.media_id for record in all_records}
    unknown_reviewed = sorted(reviewed_line_ids - known_ids)
    if unknown_reviewed:
        raise ValueError(
            "line ID file contains IDs absent from inventory: " + ", ".join(unknown_reviewed)
        )

    records = sorted(
        (
            record
            for record in all_records
            if within_scope(record, args.start_year, args.through)
        ),
        key=lambda record: (record.timestamp, record.media_id),
    )

    confirmed_line: list[Media] = []
    ambiguous_line: list[Media] = []
    shareable: list[Media] = []

    for record in records:
        confirmed = record.is_explicit_line or record.media_id in reviewed_line_ids
        ambiguous = False
        if record.is_uuid_name:
            if args.uuid_policy == "line":
                confirmed = True
            elif args.uuid_policy == "candidate" and not confirmed:
                ambiguous = True

        if confirmed:
            confirmed_line.append(record)
        elif ambiguous:
            ambiguous_line.append(record)
        else:
            shareable.append(record)

    monthly: dict[str, dict[str, object]] = {}
    records_by_month: dict[str, list[Media]] = defaultdict(list)
    for record in records:
        records_by_month[f"{record.year:04d}{record.month:02d}"].append(record)

    confirmed_ids = {record.media_id for record in confirmed_line}
    ambiguous_ids = {record.media_id for record in ambiguous_line}

    for month, month_records in sorted(records_by_month.items()):
        images = [record for record in month_records if record.kind == "image"]
        videos = [record for record in month_records if record.kind == "video"]
        confirmed_images = [
            record for record in images if record.media_id in confirmed_ids
        ]
        ambiguous_images = [
            record for record in images if record.media_id in ambiguous_ids
        ]
        outbound_images = [
            record
            for record in images
            if record.media_id not in confirmed_ids
            and record.media_id not in ambiguous_ids
        ]
        entry: dict[str, object] = {
            "media": len(month_records),
            "images": len(images),
            "videos": len(videos),
            "confirmed_line_images": len(confirmed_images),
            "ambiguous_line_images": len(ambiguous_images),
            "outbound_images": len(outbound_images),
            "status": "requires_review" if ambiguous_images else "ready",
        }
        if not args.summary_only:
            entry.update(
                {
                    "outbound_image_ids": ids(outbound_images),
                    "confirmed_line_image_ids": ids(confirmed_images),
                    "ambiguous_line_image_ids": ids(ambiguous_images),
                }
            )
        monthly[month] = entry

    confirmed_line_images = [
        record for record in confirmed_line if record.kind == "image"
    ]
    ambiguous_line_images = [
        record for record in ambiguous_line if record.kind == "image"
    ]
    adjusted = [record for record in confirmed_line_images if record.in_2350_band]
    unadjusted = [record for record in confirmed_line_images if not record.in_2350_band]

    through = None
    if args.through is not None:
        year, month = args.through
        through = {
            "month": f"{year:04d}-{month:02d}",
            "last_day": calendar.monthrange(year, month)[1],
        }

    result: dict[str, object] = {
        "schema_version": 1,
        "scope": {
            "start_year": args.start_year,
            "through": through,
            "uuid_policy": args.uuid_policy,
        },
        "totals": {
            "media": len(records),
            "images": sum(record.kind == "image" for record in records),
            "videos": sum(record.kind == "video" for record in records),
            "other": sum(record.kind == "other" for record in records),
            "confirmed_line": len(confirmed_line),
            "ambiguous_line": len(ambiguous_line),
            "outbound": len(shareable),
        },
        "filename_groups": dict(
            sorted(
                Counter(
                    "line_prefix"
                    if record.is_explicit_line
                    else "uuid"
                    if record.is_uuid_name
                    else "other"
                    for record in records
                ).items()
            )
        ),
        "date_review": {
            "confirmed_line_images": len(confirmed_line_images),
            "already_in_2350_band": len(adjusted),
            "not_in_2350_band": len(unadjusted),
        },
        "monthly": monthly,
    }

    if not args.summary_only:
        result["review"] = {
            "confirmed_line_ids": ids(confirmed_line),
            "ambiguous_line_ids": ids(ambiguous_line),
            "unadjusted_confirmed_line_image_ids": ids(unadjusted),
        }

    return result


def main() -> int:
    args = parse_args()
    try:
        plan = build_plan(args)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    payload = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(payload)
    else:
        args.output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
