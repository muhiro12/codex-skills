import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_skills_batch.py"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


class AuditSkillsBatchCLITests(unittest.TestCase):
    maxDiff = None

    def _materialize_fixture_skill_files(self, destination: Path) -> None:
        for fixture_path in destination.rglob("SKILL.fixture.md"):
            shutil.copyfile(fixture_path, fixture_path.with_name("SKILL.md"))

        for fixture_path in destination.rglob("openai.fixture.yaml"):
            shutil.copyfile(fixture_path, fixture_path.with_name("openai.yaml"))

    def _copy_fixture(self, destination_root: Path, category: str, name: str) -> Path:
        source_root = FIXTURES_DIR / category / name
        destination = destination_root / category
        shutil.copytree(source_root, destination)
        if category == "skills":
            self._materialize_fixture_skill_files(destination)
        return destination

    def _run_cli(self, repo_fixture: str, skills_fixture: str, *extra_args: str) -> str:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_root = Path(temporary_directory)
            repo_root = self._copy_fixture(temp_root, "repos", repo_fixture)
            skills_root = self._copy_fixture(temp_root, "skills", skills_fixture)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-root",
                    str(repo_root),
                    "--skills-root",
                    str(skills_root),
                    "--scope",
                    "custom",
                    *extra_args,
                ],
                capture_output=True,
                check=True,
                text=True,
            )

            return completed.stdout

    def _run_json(self, repo_fixture: str, skills_fixture: str, *extra_args: str) -> dict[str, object]:
        return json.loads(self._run_cli(repo_fixture, skills_fixture, "--format", "json", *extra_args))

    def _find_report_item(self, payload: dict[str, object], skill_name: str) -> dict[str, object]:
        for item in payload["drift_report"]:
            if item["name"] == skill_name:
                return item
        self.fail(f"Skill report not found: {skill_name}")

    def _load_script_module(self) -> object:
        module_name = "audit_skills_batch_test_module"
        spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
        if spec is None or spec.loader is None:
            self.fail("Unable to load audit script module")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def test_repo_specific_detection_uses_generic_concrete_references(self) -> None:
        module = self._load_script_module()
        repo_specific_text = (
            "Develop `ClientPortal/` while treating `../DesignSystem` and "
            "`../SharedKit` as read-only references."
        ).lower()
        generic_sibling_text = (
            "Use a locally available sibling reference repository as a read-only fallback."
        ).lower()

        self.assertEqual(
            module.infer_execution_family(repo_specific_text),
            "repo_specific_development",
        )
        self.assertEqual(module.infer_scope_family(repo_specific_text), "repo_specific")
        self.assertEqual(module.infer_execution_family(generic_sibling_text), "general_analysis")
        self.assertEqual(module.infer_scope_family(generic_sibling_text), "repo_agnostic")

    def test_overview_doc_resolution_uses_generic_current_overview_suffix(self) -> None:
        module = self._load_script_module()

        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            docs_dir = repo_root / "docs"
            docs_dir.mkdir()
            (docs_dir / "alpha-current-overview.md").write_text("# Alpha\n", encoding="utf-8")

            ground_truth = module.extract_ground_truth(repo_root, include_doc_source=True)

        self.assertTrue(ground_truth["optional_doc_source_used"])
        self.assertIn("docs/alpha-current-overview.md", ground_truth["sources_read"])

    def test_refresh_markdown_output_uses_mode_sections_and_recommendation_cap(self) -> None:
        output = self._run_cli("with_ci", "mixed", "--format", "markdown")

        self.assertIn("1) refresh 提案（優先順）", output)
        self.assertIn("2) 採用判断材料", output)
        self.assertIn("3) maintenance に回せる整合性候補", output)
        self.assertIn("- モード: refresh", output)
        self.assertIn("- refresh では自動適用用の更新本文を出力しません。", output)
        self.assertNotIn("--- SKILL: internal-fixture-ci-drift-skill ---", output)

        recommendation_block = output.split("3) maintenance に回せる整合性候補", 1)[1].strip().splitlines()
        recommendation_lines = [
            line
            for line in recommendation_block
            if line.startswith("- ") and not line.startswith("- maintenance 候補:")
        ]
        self.assertEqual(len(recommendation_lines), 3)

    def test_maintenance_markdown_output_reports_applied_fixes(self) -> None:
        output = self._run_cli("with_ci", "mixed", "--format", "markdown", "--mode", "maintenance")

        self.assertIn("1) maintenance 実施結果", output)
        self.assertIn("2) 自動適用した整合性修正", output)
        self.assertIn("3) refresh に回した判断事項", output)
        self.assertIn("- モード: maintenance", output)
        self.assertIn("- internal-fixture-ci-drift-skill:", output)
        self.assertIn("- internal-fixture-prompt-drift-skill:", output)
        self.assertIn("issue codes: ci_entrypoint_not_aligned, ci_policy_not_dynamic", output)
        self.assertIn("issue codes: default_prompt_missing_skill_reference", output)
        self.assertNotIn("--- SKILL: internal-fixture-ci-drift-skill ---", output)

    def test_ci_alignment_checks_are_skipped_without_ground_truth(self) -> None:
        payload = self._run_json("without_ci", "mixed")

        ground_truth = payload["ground_truth"]
        self.assertEqual(ground_truth["canonical_entrypoint"], "")
        self.assertFalse(ground_truth["ci_ground_truth_available"])

        ci_drift_item = self._find_report_item(payload, "internal-fixture-ci-drift-skill")
        self.assertEqual(ci_drift_item["status"], "aligned")
        self.assertNotIn("ci_entrypoint_not_aligned", ci_drift_item["issue_codes"])
        self.assertNotIn("ci_policy_not_dynamic", ci_drift_item["issue_codes"])

    def test_include_self_opt_in_controls_self_audit(self) -> None:
        default_payload = self._run_json("without_ci", "mixed")
        default_names = {item["name"] for item in default_payload["drift_report"]}
        self.assertNotIn("internal-fixture-self-audit-skills-batch-auditor", default_names)
        self.assertNotIn("internal-fixture-nested-fixture-skill", default_names)

        with_self_payload = self._run_json("without_ci", "mixed", "--include-self")
        with_self_names = {item["name"] for item in with_self_payload["drift_report"]}
        self.assertIn("internal-fixture-self-audit-skills-batch-auditor", with_self_names)

    def test_openai_interface_parser_supports_quote_variants(self) -> None:
        payload = self._run_json("without_ci", "quote_variants")

        for skill_name in [
            "internal-fixture-double-quoted-skill",
            "internal-fixture-single-quoted-skill",
            "internal-fixture-bare-scalar-skill",
        ]:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["issue_codes"], [])

    def test_internal_visibility_allows_missing_openai_yaml(self) -> None:
        payload = self._run_json("without_ci", "mixed")

        item = self._find_report_item(payload, "internal-fixture-visibility-skill")
        self.assertEqual(item["status"], "aligned")
        self.assertEqual(item["visibility"], "internal")
        self.assertNotIn("missing_openai_yaml", item["issue_codes"])

    def test_xcode_managed_external_is_excluded_from_custom_drift_report(self) -> None:
        payload = self._run_json("without_ci", "xcode_classification")

        drift_names = {item["name"] for item in payload["drift_report"]}
        self.assertIn("internal-fixture-regular-custom-skill", drift_names)
        self.assertNotIn("xcode-skill-managed-fixture", drift_names)
        self.assertNotIn("internal-fixture-system-skill", drift_names)

        sync_report = payload["xcode_sync_report"]
        self.assertEqual(sync_report["managed_external_count"], 1)
        self.assertEqual(sync_report["unmanaged_xcode_prefix_count"], 1)
        self.assertEqual(sync_report["managed_external"][0]["name"], "xcode-skill-managed-fixture")
        self.assertEqual(sync_report["managed_external"][0]["status"], "aligned")
        self.assertEqual(sync_report["managed_external"][0]["issues"], [])

    def test_unmanaged_xcode_prefix_is_reported_as_risky(self) -> None:
        payload = self._run_json("without_ci", "xcode_classification")

        item = self._find_report_item(payload, "xcode-skill-unmanaged-collision")
        self.assertEqual(item["classification"], "unmanaged-xcode-prefix")
        self.assertEqual(item["status"], "risky")
        self.assertIn("unmanaged_xcode_prefix", item["issue_codes"])
        self.assertEqual(item["maintenance_issue_codes"], [])
        self.assertIn("unmanaged_xcode_prefix", item["refresh_issue_codes"])

    def test_named_xcode_managed_external_stays_sync_only(self) -> None:
        payload = self._run_json(
            "without_ci",
            "xcode_classification",
            "--skill",
            "xcode-skill-managed-fixture",
        )

        self.assertEqual(payload["drift_report"], [])
        self.assertEqual(payload["xcode_sync_report"]["status"], "aligned")
        self.assertEqual(payload["xcode_sync_report"]["managed_external_count"], 1)
        self.assertEqual(
            payload["xcode_sync_report"]["managed_external"][0]["name"],
            "xcode-skill-managed-fixture",
        )

    def test_prioritization_output_includes_scores_classification_and_actions(self) -> None:
        payload = self._run_json("without_ci", "prioritization")

        core_item = self._find_report_item(payload, "internal-fixture-core-keeper-skill")
        self.assertEqual(core_item["portfolio_classification"], "core")
        self.assertEqual(core_item["recommended_action"], "keep as-is")
        self.assertEqual(
            set(core_item["scores"]),
            {
                "reuse value",
                "clarity of invocation",
                "safety",
                "maintenance burden",
            },
        )

        improve_item = self._find_report_item(payload, "internal-fixture-improve-next-skill")
        self.assertEqual(improve_item["portfolio_classification"], "useful")
        self.assertEqual(improve_item["recommended_action"], "improve next")
        self.assertIn("default_prompt_missing_skill_reference", improve_item["issue_codes"])

        merge_item = self._find_report_item(payload, "internal-fixture-overview-refresh-skill")
        self.assertEqual(merge_item["portfolio_classification"], "optional")
        self.assertEqual(merge_item["recommended_action"], "merge with another skill")
        self.assertEqual(merge_item["merge_target"], "internal-fixture-overview-sync-skill")

        specialized_item = self._find_report_item(payload, "internal-fixture-specialized-keeper-skill")
        self.assertEqual(specialized_item["portfolio_classification"], "useful")
        self.assertEqual(specialized_item["recommended_action"], "keep as-is")
        self.assertEqual(specialized_item["scores"]["maintenance burden"], 3)

        retire_item = self._find_report_item(payload, "internal-fixture-retire-candidate-skill")
        self.assertEqual(retire_item["portfolio_classification"], "retire candidate")
        self.assertEqual(retire_item["recommended_action"], "retire")
        self.assertIn("recursive_generated_scan", retire_item["issue_codes"])

        batch_decisions = payload["batch_decisions"]
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["keep as-is"]],
            [
                "internal-fixture-specialized-keeper-skill",
                "internal-fixture-core-keeper-skill",
                "internal-fixture-overview-sync-skill",
            ],
        )
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["improve next"]],
            ["internal-fixture-improve-next-skill"],
        )
        self.assertEqual(
            [
                (entry["name"], entry["merge_target"])
                for entry in batch_decisions["merge with another skill"]
            ],
            [
                (
                    "internal-fixture-overview-refresh-skill",
                    "internal-fixture-overview-sync-skill",
                )
            ],
        )
        self.assertEqual(
            [entry["name"] for entry in batch_decisions["retire"]],
            ["internal-fixture-retire-candidate-skill"],
        )

    def test_markdown_output_lists_batch_decision_buckets_in_japanese_report(self) -> None:
        output = self._run_cli("without_ci", "prioritization", "--format", "markdown")

        self.assertIn(
            "- keep as-is: internal-fixture-specialized-keeper-skill, internal-fixture-core-keeper-skill, internal-fixture-overview-sync-skill",
            output,
        )
        self.assertIn("- improve next: internal-fixture-improve-next-skill", output)
        self.assertIn(
            "- merge with another skill: internal-fixture-overview-refresh-skill -> internal-fixture-overview-sync-skill",
            output,
        )
        self.assertIn("- retire: internal-fixture-retire-candidate-skill", output)
        self.assertIn("  - 評価軸スコア:", output)
        self.assertIn("  - 分類: core", output)
        self.assertIn("  - 推奨アクション: improve next", output)

    def test_maintenance_mode_separates_candidates_and_refresh_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_root = Path(temporary_directory)
            repo_root = self._copy_fixture(temp_root, "repos", "with_ci")
            skills_root = self._copy_fixture(temp_root, "skills", "mixed")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-root",
                    str(repo_root),
                    "--skills-root",
                    str(skills_root),
                    "--scope",
                    "custom",
                    "--format",
                    "json",
                    "--mode",
                    "maintenance",
                ],
                capture_output=True,
                check=True,
                text=True,
            )
            payload = json.loads(completed.stdout)

            ci_skill_text = (skills_root / "ci-drift-skill" / "SKILL.md").read_text(
                encoding="utf-8"
            )
            prompt_openai_text = (
                skills_root / "prompt-drift-skill" / "agents" / "openai.yaml"
            ).read_text(encoding="utf-8")

        mode_result = payload["mode_result"]
        self.assertEqual(mode_result["mode"], "maintenance")
        self.assertEqual(mode_result["maintenance_candidates"], [])
        self.assertIn("internal-fixture-refresh-review-skill", mode_result["refresh_candidates"])
        self.assertIn("internal-fixture-scan-drift-skill", mode_result["refresh_candidates"])
        self.assertEqual(
            [
                (entry["name"], entry["issue_codes"])
                for entry in mode_result["applied_fixes"]
            ],
            [
                (
                    "internal-fixture-ci-drift-skill",
                    ["ci_entrypoint_not_aligned", "ci_policy_not_dynamic"],
                ),
                (
                    "internal-fixture-prompt-drift-skill",
                    ["default_prompt_missing_skill_reference"],
                ),
            ],
        )

        ci_drift_item = self._find_report_item(payload, "internal-fixture-ci-drift-skill")
        self.assertEqual(ci_drift_item["status"], "aligned")
        self.assertEqual(ci_drift_item["maintenance_issue_codes"], [])
        self.assertEqual(ci_drift_item["refresh_issue_codes"], [])
        self.assertIn("bash ci_scripts/tasks/verify_task_completion.sh", ci_skill_text)
        self.assertNotIn("bash ci_scripts/tasks/run_required_builds.sh", ci_skill_text)

        refresh_item = self._find_report_item(payload, "internal-fixture-refresh-review-skill")
        self.assertEqual(refresh_item["maintenance_issue_codes"], [])
        self.assertIn("missing_openai_yaml", refresh_item["refresh_issue_codes"])

        scan_item = self._find_report_item(payload, "internal-fixture-scan-drift-skill")
        self.assertEqual(scan_item["maintenance_issue_codes"], [])
        self.assertIn("generated_directory_guard_missing", scan_item["refresh_issue_codes"])
        self.assertIn("$internal-fixture-prompt-drift-skill", prompt_openai_text)

    def test_distinct_roles_fixture_blocks_false_positive_merge_targets(self) -> None:
        payload = self._run_json("without_ci", "distinct_roles")

        kept_skill_names = [
            "internal-fixture-release-risk-skill",
            "internal-fixture-app-store-release-notes-skill",
            "internal-fixture-footprint-diagnosis-skill",
            "internal-fixture-skills-portfolio-auditor-skill",
            "internal-fixture-swiftdata-schema-skill",
            "internal-fixture-ci-push-readiness-skill",
            "internal-fixture-repo-momentum-skill",
            "internal-fixture-repo-specific-dev-skill",
        ]

        for skill_name in kept_skill_names:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["recommended_action"], "keep as-is")
            self.assertEqual(item["merge_target"], "")

        self.assertEqual(
            [entry["name"] for entry in payload["batch_decisions"]["merge with another skill"]],
            [],
        )

    def test_verify_bootstrap_and_contract_maintenance_stay_separate(self) -> None:
        payload = self._run_json("without_ci", "distinct_verify_roles")

        for skill_name in [
            "internal-fixture-apple-verify-bootstrap-skill",
            "internal-fixture-verify-contract-maintenance-skill",
        ]:
            item = self._find_report_item(payload, skill_name)
            self.assertEqual(item["status"], "aligned")
            self.assertEqual(item["recommended_action"], "keep as-is")
            self.assertEqual(item["merge_target"], "")

        self.assertEqual(
            [entry["name"] for entry in payload["batch_decisions"]["merge with another skill"]],
            [],
        )


if __name__ == "__main__":
    unittest.main()
