# GRAVEYARD Demo Video Script (~5 minutes)

Record this on SIFT or locally with bundled sample exports. Show terminal + Cursor side by side.

---

## [0:00–0:30] Hook — "The Graveyard Problem"

**Screen:** Title slide or README

**Narration:**
> "Memory forensics agents find evil — but they also hallucinate it. GRAVEYARD hunts ghost artifacts: processes that exist in memory scans but not in active process lists, and network sockets with no live process. And when the AI overclaims, our verifier forces autonomous self-correction."

**Action:** Show README tagline and architecture diagram from `docs/ARCHITECTURE.md`.

---

## [0:30–1:30] Setup — Sample case

**Screen:** Terminal

**Narration:**
> "We bundled a sample case with a ghost PID 5678 — PowerShell visible in psscan but hidden from pslist."

**Commands:**
```bash
cd graveyard
ls examples/sample_exports/
head -5 examples/sample_exports/psscan_20240315.txt
grep 5678 examples/sample_exports/psscan_20240315.txt
grep 5678 examples/sample_exports/pslist_20240315.txt || echo "NOT in pslist — ghost!"
```

**Highlight:** PID 5678 in psscan, absent from pslist.

---

## [1:30–2:30] Core demo — graveyard_correlate.py

**Screen:** Terminal

**Narration:**
> "GRAVEYARD's correlator is deterministic — no LLM guessing. It diffs psscan against pslist and flags orphan ESTABLISHED sockets."

**Commands:**
```bash
python3 graveyard_correlate.py --exports examples/sample_exports
```

**Highlight:** JSON output showing:
- `"ghost_count": 1` — PID 5678
- `"orphan_socket_count": 1` — 198.51.100.42:4444

**Narration:**
> "One ghost, one orphan socket — both with line-level citations back to the raw exports."

---

## [2:30–3:30] Self-correction — verifier REJECT

**Screen:** Terminal + optionally show `findings_draft_v1_reject.json`

**Narration:**
> "Now the agent drafts findings. Version 1 overclaims — it calls cmd.exe a malicious C2 beacon in the observation field. The verifier rejects it."

**Commands:**
```bash
python3 verify_findings.py examples/findings_draft_v1_reject.json \
  --exports examples/sample_exports --json-out
echo "Exit code: $?"
```

**Highlight:** REJECT output:
- `ATTRIBUTION_GUARD` — "malicious", "C2", "attacker"
- `CONFIDENCE_GUARD` — "confirmed" with 1 citation

**Narration:**
> "The agent must self-correct. No arguing with the verifier."

---

## [3:30–4:30] Self-correction — verifier PASS

**Screen:** Terminal

**Narration:**
> "Version 2 moves attribution to interpretation, cites exact export substrings, and uses inferred confidence."

**Commands:**
```bash
python3 verify_findings.py examples/findings_draft_v2_pass.json \
  --exports examples/sample_exports --report reports/report.md
echo "Exit code: $?"
cat reports/report.md
```

**Highlight:** PASSED message, generated report with observation/interpretation separation.

**Narration:**
> "Report only generates after verification passes. Every claim is grep-able in the exports."

---

## [4:30–5:00] Close — tiebreaker + links

**Screen:** Architecture diagram or execution logs

**Narration:**
> "GRAVEYARD wins on the tiebreaker: autonomous self-correction with a full audit trail. Deterministic ghost detection plus architectural verification — not just prompt engineering. GitHub link in description. Built for FIND EVIL! on Protocol SIFT."

**Show:** `docs/execution_logs/execution_log.jsonl` — timestamped tool + verifier events.

**End card:** GitHub URL, Devpost submission, your name/team.

---

## Recording tips

- Use 1080p terminal font size 14+
- Pause on REJECT output for 3 seconds — judges need to read it
- Optional: show Cursor agent following AGENTS.md triage sequence on live SIFT
- Keep under 5:00 — cut the setup section if running long
