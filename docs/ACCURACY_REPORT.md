# GRAVEYARD Accuracy Report

Evaluation against bundled sample case (`examples/sample_exports/`) and verifier self-correction demo. Regenerated **2026-06-16** for FIND EVIL submission.

## Ground truth (sample case)

| Artifact | Expected | Detected by correlate | Cited in v2 findings |
|----------|----------|----------------------|---------------------|
| Ghost PID 5678 (powershell.exe) | Present in psscan, absent pslist | Yes | F001 |
| Orphan socket PID 5678 → 198.51.100.42:4444 | ESTABLISHED, PID not in pslist | Yes | F003 |
| Live PID 1234 → 203.0.113.5:443 | ESTABLISHED, PID in pslist | Not orphan (correct) | F002 |

## Finding confidence breakdown (v2_pass)

| ID | Confidence | Status | Basis |
|----|-----------|--------|-------|
| F001 | inferred | Correct | Single-source ghost diff (psscan vs pslist) |
| F002 | inferred | Correct | netscan + psscan cross-reference |
| F003 | inferred | Correct | netscan orphan + pslist absence |

No findings marked `confirmed` — insufficient independent corroboration for confirmed tier (by design).

## False positives

| Check | Result |
|-------|--------|
| PID 456 (winlogon.exe) in pslist only | Not flagged as ghost — correct |
| PID 1234 ESTABLISHED connection | Not flagged as orphan (in pslist) — correct |
| System PID 4 | Present in both lists — not flagged |

**False positive rate on sample case: 0/3 detections**

## False negatives

| Potential miss | Status | Notes |
|---------------|--------|-------|
| Hollow memory (malfind) | Not in sample exports | Requires live malfind run; AGENTS.md step 7 covers this |
| UDP orphan sockets | Not tested | Correlator filters ESTABLISHED only (by design) |
| Ghost PPID chain analysis | Not implemented | Future enhancement |

## Overclaim caught (self-correction demo)

`findings_draft_v1_reject.json` F002 observation:

> "Process 1234 is malicious C2 beacon communicating with attacker infrastructure"

Verifier rejections:
- **ATTRIBUTION_GUARD** — "malicious", "C2", "attacker" in observation
- **CONFIDENCE_GUARD** — "confirmed" with only 1 citation

Corrected in v2:

> observation: "PID 1234 (cmd.exe) has an ESTABLISHED TCP connection to 203.0.113.5 on port 443."

Attribution moved to interpretation with `inferred` confidence.

## Spoliation & constraint bypass (honest assessment)

| Control | Mechanism | Bypass if agent ignores? |
|---------|-----------|--------------------------|
| Evidence image writes | **Prompt-only** (`AGENTS.md`, Cursor rules) | Yes — agent could run `rm`/`mv` on evidence if shell is unrestricted |
| Export tee discipline | **Prompt-only** | Yes — agent could skip teeing or edit exports |
| Finding citations | **Architectural** (`verify_findings.py`) | No — CITATION_MISMATCH / PHANTOM_ARTIFACT reject fabricated substrings |
| Attribution in observations | **Architectural** | No — ATTRIBUTION_GUARD blocks 14 intent terms in observation field |
| Report generation | **Architectural** | No — exit code 1 blocks `reports/report.md` |
| MCP tool surface | **Architectural** (`mcp_graveyard_server.py`) | No shell exposed — only correlate + verify on existing paths |

**Spoliation test (verifier layer):** Adding `"PID 9999 (evil.exe) in psscan"` without export backing → **PHANTOM_ARTIFACT** REJECT. The verifier reads exports as read-only; it cannot prevent deletion of the original memory image — that requires OS-level read-only mounts or an allowlist kernel (as in heavier submissions). We document this gap rather than claim full spoliation prevention.

**Failure mode when model ignores prompt:** Agent could modify `exports/` text files; verifier would then accept citations against tampered exports. Mitigation for production: mount evidence read-only at OS level; treat `exports/` as append-only with hashes at capture time.

## Baseline comparison

| Approach | Ghost detection | Ghost-first sequencing | Attribution control | Self-correction gate | Audit trail |
|----------|----------------|------------------------|--------------------|-----------------------|-------------|
| Raw Volatility manual | Analyst diff | Manual | Manual | Manual | Analyst notes |
| LLM-only triage | Unreliable | None | None | None | Chat history |
| Protocol SIFT baseline | Agent judgment | No — blanket netscan | Prompt-only | Optional | Partial |
| EvidenceChain ghost rule | Contradiction detector (1 of 7) | Part of multi-pass review | Architectural (MCP + phantom) | 4-pass engine | Signed receipts |
| **GRAVEYARD** | Deterministic correlate | **Yes — netscan only on flagged PIDs** | Architectural verifier | **Mandatory exit-code loop** | JSONL logs |

### Differentiation vs EvidenceChain ghost detector

EvidenceChain catches ghosts as one contradiction type among seven across disk+memory+timeline. GRAVEYARD **leads with ghosts**: `graveyard_correlate.py` runs immediately after psscan/pslist (before netscan), focuses agent attention on flagged PIDs only, and pairs detection with an **exit-code verifier** the agent cannot argue with. Tradeoff: GRAVEYARD is memory-narrower but ~300 lines, reproducible offline in 30 seconds via `run_demo.ps1`.

## Metrics summary

| Metric | Value |
|--------|-------|
| Ghost recall (sample) | 1/1 (100%) |
| Orphan recall (sample) | 1/1 (100%) |
| False positives (sample) | 0 |
| Overclaim blocked | 1/1 (100%) |
| Self-correction success | v1 REJECT → v2 PASS |

## Limitations

- Correlator matches on PID only; does not detect DKOM or name spoofing
- Requires correctly formatted Volatility 3 tabular exports
- malfind hollow detection depends on agent following AGENTS.md step 7
- Single synthetic sample case — live SIFT validation recommended before production claims
- Evidence-image spoliation prevention is prompt-only; verifier layer is architectural
