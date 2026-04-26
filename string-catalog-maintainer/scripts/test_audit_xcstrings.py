#!/usr/bin/env python3
"""Regression tests for audit_xcstrings.py."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_xcstrings.py")


def string_unit(value: str, state: str = "translated") -> dict:
    return {
        "stringUnit": {
            "state": state,
            "value": value,
        }
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class AuditXCStringsTests(unittest.TestCase):
    def run_audit(self, project_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--project-root",
                str(project_root),
                *args,
                "--format",
                "json",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if check and result.returncode != 0:
            self.fail(f"audit failed: {result.stderr}\n{result.stdout}")
        return result

    def test_infers_missing_locale_from_sibling_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_json(
                root / "App/Resources/Localizable.xcstrings",
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "Sibling": {
                            "localizations": {
                                "en": string_unit("Sibling"),
                                "ja": string_unit("Kyodai"),
                            }
                        }
                    },
                },
            )
            write_json(
                root / "Lib/Resources/Localizable.xcstrings",
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "Hello": {
                            "localizations": {
                                "en": string_unit("Hello"),
                            }
                        }
                    },
                },
            )

            report = json.loads(self.run_audit(root).stdout)
            lib_report = next(
                catalog for catalog in report["catalogs"]
                if catalog["path"] == "Lib/Resources/Localizable.xcstrings"
            )

            self.assertEqual(lib_report["required_locales"], ["en", "ja"])
            self.assertEqual(lib_report["incomplete_keys"][0]["missing_locales"], ["ja"])
            self.assertEqual(lib_report["translation_tasks"][0]["reasons"], ["missing-locale"])

    def test_reports_new_state_and_source_copy_as_translation_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_json(
                root / "Resources/Localizable.xcstrings",
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "Hello": {
                            "localizations": {
                                "en": string_unit("Hello"),
                                "ja": string_unit("Hello", state="new"),
                            }
                        }
                    },
                },
            )

            report = json.loads(
                self.run_audit(root, "--required-locales", "en,ja").stdout
            )
            task = report["catalogs"][0]["translation_tasks"][0]

            self.assertEqual(task["key"], "Hello")
            self.assertEqual(task["locale"], "ja")
            self.assertIn("state-new", task["reasons"])
            self.assertIn("source-copy", task["reasons"])

    def test_applies_string_unit_translation_patch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalog_path = root / "Resources/Localizable.xcstrings"
            patch_path = root / "patch.json"
            write_json(
                catalog_path,
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "%lld marks": {
                            "localizations": {
                                "en": string_unit("%lld marks"),
                                "ja": string_unit("%lld marks", state="new"),
                            }
                        }
                    },
                },
            )
            write_json(
                patch_path,
                {
                    "translations": [
                        {
                            "catalog": "Resources/Localizable.xcstrings",
                            "key": "%lld marks",
                            "locale": "ja",
                            "path": ["stringUnit"],
                            "value": "%lld marcas",
                        }
                    ]
                },
            )

            report = json.loads(
                self.run_audit(
                    root,
                    "--translation-patch",
                    str(patch_path),
                    "--apply-translations",
                ).stdout
            )
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            unit = catalog["strings"]["%lld marks"]["localizations"]["ja"]["stringUnit"]

            self.assertEqual(unit["state"], "translated")
            self.assertEqual(unit["value"], "%lld marcas")
            self.assertEqual(len(report["catalogs"][0]["translation_patch"]["applied_entries"]), 1)

    def test_rejects_placeholder_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalog_path = root / "Resources/Localizable.xcstrings"
            patch_path = root / "patch.json"
            write_json(
                catalog_path,
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "%lld marks": {
                            "localizations": {
                                "en": string_unit("%lld marks"),
                                "ja": string_unit("%lld marks", state="new"),
                            }
                        }
                    },
                },
            )
            write_json(
                patch_path,
                {
                    "translations": [
                        {
                            "catalog": "Resources/Localizable.xcstrings",
                            "key": "%lld marks",
                            "locale": "ja",
                            "path": ["stringUnit"],
                            "value": "marcas",
                        }
                    ]
                },
            )

            result = self.run_audit(
                root,
                "--translation-patch",
                str(patch_path),
                "--apply-translations",
                check=False,
            )
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
            unit = catalog["strings"]["%lld marks"]["localizations"]["ja"]["stringUnit"]

            self.assertEqual(result.returncode, 1)
            self.assertIn("placeholder mismatch", result.stdout)
            self.assertEqual(unit["state"], "new")
            self.assertEqual(unit["value"], "%lld marks")

    def test_classifies_stale_unused_strong_and_weak_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            write_json(
                root / "Resources/Localizable.xcstrings",
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "Unused stale": {
                            "extractionState": "stale",
                            "localizations": {"en": string_unit("Unused stale")},
                        },
                        "Live stale": {
                            "extractionState": "stale",
                            "localizations": {"en": string_unit("Live stale")},
                        },
                        "%lld marks": {
                            "extractionState": "stale",
                            "localizations": {"en": string_unit("%lld marks")},
                        },
                    },
                },
            )
            source_path = root / "Sources/View.swift"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text(
                'Text("Live stale")\nText("\\(count) marks")\n',
                encoding="utf-8",
            )

            catalog = json.loads(self.run_audit(root).stdout)["catalogs"][0]

            self.assertEqual(catalog["stale_key_count"], 3)
            self.assertEqual(catalog["raw_stale_marker_count"], 3)
            self.assertTrue(catalog["stale_marker_count_matches"])
            self.assertEqual(
                [entry["key"] for entry in catalog["stale_unused_candidates"]],
                ["Unused stale"],
            )
            self.assertEqual(
                [entry["key"] for entry in catalog["stale_strong_referenced_keys"]],
                ["Live stale"],
            )
            self.assertEqual(
                [entry["key"] for entry in catalog["stale_weak_referenced_keys"]],
                ["%lld marks"],
            )

    def test_applies_string_set_and_plural_variation_patches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            catalog_path = root / "Resources/Localizable.xcstrings"
            patch_path = root / "patch.json"
            write_json(
                catalog_path,
                {
                    "sourceLanguage": "en",
                    "strings": {
                        "Check ${applicationName}": {
                            "localizations": {
                                "en": {
                                    "stringSet": {
                                        "state": "translated",
                                        "values": [
                                            "Check ${applicationName}",
                                            "Open ${applicationName}",
                                        ],
                                    }
                                },
                                "ja": {
                                    "stringSet": {
                                        "state": "new",
                                        "values": [
                                            "Check ${applicationName}",
                                            "Open ${applicationName}",
                                        ],
                                    }
                                },
                            }
                        },
                        "%lld Items": {
                            "localizations": {
                                "en": {
                                    "variations": {
                                        "plural": {
                                            "one": string_unit("%lld Item"),
                                            "other": string_unit("%lld Items"),
                                        }
                                    }
                                },
                                "ja": {
                                    "variations": {
                                        "plural": {
                                            "one": string_unit("%lld Item", state="new"),
                                            "other": string_unit("%lld Items", state="new"),
                                        }
                                    }
                                },
                            }
                        },
                    },
                },
            )
            write_json(
                patch_path,
                {
                    "translations": [
                        {
                            "catalog": "Resources/Localizable.xcstrings",
                            "key": "Check ${applicationName}",
                            "locale": "ja",
                            "path": ["stringSet"],
                            "values": [
                                "Check ${applicationName} ja",
                                "Open ${applicationName} ja",
                            ],
                        },
                        {
                            "catalog": "Resources/Localizable.xcstrings",
                            "key": "%lld Items",
                            "locale": "ja",
                            "path": ["variations", "plural", "one", "stringUnit"],
                            "value": "%lld item ja",
                        },
                        {
                            "catalog": "Resources/Localizable.xcstrings",
                            "key": "%lld Items",
                            "locale": "ja",
                            "path": ["variations", "plural", "other", "stringUnit"],
                            "value": "%lld items ja",
                        },
                    ]
                },
            )

            report = json.loads(
                self.run_audit(
                    root,
                    "--translation-patch",
                    str(patch_path),
                    "--apply-translations",
                ).stdout
            )
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

            string_set = catalog["strings"]["Check ${applicationName}"]["localizations"]["ja"]["stringSet"]
            plural = catalog["strings"]["%lld Items"]["localizations"]["ja"]["variations"]["plural"]
            self.assertEqual(string_set["state"], "translated")
            self.assertEqual(plural["one"]["stringUnit"]["state"], "translated")
            self.assertEqual(plural["other"]["stringUnit"]["state"], "translated")
            self.assertEqual(len(report["catalogs"][0]["translation_patch"]["applied_entries"]), 3)


if __name__ == "__main__":
    unittest.main()
