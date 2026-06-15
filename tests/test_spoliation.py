#!/usr/bin/env python3
"""GRAVEYARD spoliation test suite — architectural + documented controls."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from spoliation_guard import (  # noqa: E402
    ALLOWED_WRITE_ROOTS,
    check_path_write_policy,
    evidence_path_patterns_in_script,
    export_dir_writable,
    is_evidence_path,
    is_allowed_write_path,
    parse_reject_codes,
)
from verify_findings import verify_findings  # noqa: E402


class TestEvidencePathBlocking(unittest.TestCase):
    def test_cases_evidence_path_blocked(self):
        allowed, reason = check_path_write_policy("/cases/graveyard/evidence/mem.raw")
        self.assertFalse(allowed)
        self.assertIn("EVIDENCE_PATH_BLOCKED", reason)

    def test_mnt_path_blocked(self):
        self.assertTrue(is_evidence_path("/mnt/evidence/disk.e01"))

    def test_exports_path_allowed(self):
        allowed, _ = check_path_write_policy("exports/pslist_20240315.txt")
        self.assertTrue(allowed)

    def test_random_path_outside_roots_blocked(self):
        allowed, reason = check_path_write_policy("/tmp/evil_write.txt")
        self.assertFalse(allowed)
        self.assertIn("WRITE_OUTSIDE_ALLOWED_ROOTS", reason)


class TestAllowedWriteRoots(unittest.TestCase):
    def test_all_roots_recognized(self):
        for root in ALLOWED_WRITE_ROOTS:
            self.assertTrue(is_allowed_write_path(f"{root}/test.txt"))

    def test_analysis_reports_docs(self):
        for root in ("analysis", "reports", "docs"):
            self.assertTrue(is_allowed_write_path(f"{root}/subdir/file.json"))


class TestExportDirectoryAccess(unittest.TestCase):
    def test_sample_exports_writable(self):
        exports = REPO_ROOT / "examples" / "sample_exports"
        self.assertTrue(exports.is_dir())
        self.assertTrue(export_dir_writable(exports))

    def test_readonly_check_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "exports"
            p.mkdir()
            if os.name != "nt":
                os.chmod(p, 0o555)
                from spoliation_guard import export_dir_exists_readonly
                self.assertTrue(export_dir_exists_readonly(p))
                os.chmod(p, 0o755)


class TestVerifierHallucinationGuard(unittest.TestCase):
    def setUp(self):
        self.exports = REPO_ROOT / "examples" / "sample_exports"

    def test_phantom_pid_rejected(self):
        finding = {
            "id": "F999",
            "observation": "PID 9999 (evil.exe) appears in psscan output but is absent from pslist.",
            "interpretation": "Ghost",
            "confidence": "inferred",
            "citations": [
                {"export_file": "psscan_20240315.txt", "matched_text": "9999\t1234\tevil.exe"}
            ],
            "tool_provenance": {"command": "test", "timestamp": "2024-03-15T10:00:00Z"},
        }
        _, errors = verify_findings([finding], self.exports)
        codes = parse_reject_codes(errors)
        self.assertIn("PHANTOM_ARTIFACT", codes)

    def test_attribution_guard_rejected(self):
        finding = {
            "id": "F998",
            "observation": "Process 1234 is malicious C2 beacon with attacker infrastructure",
            "interpretation": "Bad",
            "confidence": "confirmed",
            "citations": [
                {
                    "export_file": "netscan_20240315.txt",
                    "matched_text": "1234\t192.168.1.105\t203.0.113.5\t443\tESTABLISHED",
                }
            ],
            "tool_provenance": {"command": "test", "timestamp": "2024-03-15T10:00:00Z"},
        }
        _, errors = verify_findings([finding], self.exports)
        codes = parse_reject_codes(errors)
        self.assertIn("ATTRIBUTION_GUARD", codes)


class TestLiveTriageScriptDocumentation(unittest.TestCase):
    def test_run_live_triage_documents_evidence_patterns(self):
        script = (REPO_ROOT / "scripts" / "run_live_triage.sh").read_text(encoding="utf-8")
        self.assertTrue(evidence_path_patterns_in_script(script))
        self.assertIn("EVIDENCE_PATTERNS", script)


class TestGroundTruthHallucinationSuite(unittest.TestCase):
    def test_ground_truth_hallucination_tests_reject(self):
        gt_path = REPO_ROOT / "examples" / "ground_truth_srl2018_sample.json"
        gt = json.loads(gt_path.read_text(encoding="utf-8"))
        exports = REPO_ROOT / "examples" / "sample_exports"
        caught = 0
        for test in gt.get("hallucination_tests", []):
            _, errors = verify_findings([test["finding"]], exports)
            if errors:
                caught += 1
        self.assertEqual(caught, len(gt.get("hallucination_tests", [])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
