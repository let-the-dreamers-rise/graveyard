# Devpost Submission — GRAVEYARD

Copy sections below into the [FIND EVIL! Devpost](https://find-evil.devpost.com/) form.

---

## Project name

**GRAVEYARD**

## Tagline

Hunt ghost artifacts in Windows memory with deterministic detection and autonomous self-correction.

## Inspiration

AI memory forensics agents can find suspicious PIDs — but they also hallucinate "malicious C2 beacons" without evidence. We built GRAVEYARD because the graveyard of terminated processes and orphan sockets is where real evil hides, and agents need hard guardrails to prove their claims.

## What it does

GRAVEYARD extends Protocol SIFT with:

1. **`graveyard_correlate.py`** — Deterministic detection of ghost processes (psscan − pslist) and orphan sockets (ESTABLISHED connections without live processes)
2. **`verify_findings.py`** — Citation verifier that blocks attribution in observations and triggers agent self-correction
3. **Agent playbook** — `AGENTS.md` + Cursor rules for ghost-first triage on SANS SIFT

The agent runs Volatility, correlates ghosts, drafts findings, gets REJECTed on overclaims, self-corrects, and only then generates a verified report.

## How we built it

- **Protocol SIFT** for agent orchestration on SANS SIFT Workstation
- **Python 3** for deterministic correlate + verifier (no ML, no API calls)
- **Volatility 3** exports as the sole source of truth
- **JSON Schema** finding contract with observation/interpretation separation
- **Cursor rules** (`.cursor/rules/graveyard.mdc`) for always-on agent guardrails
- **JSONL audit logs** for every tool run and verifier pass/reject

Architecture separates prompt guardrails (AGENTS.md) from architectural guardrails (correlator + verifier exit codes).

## Challenges we ran into

1. **Observation vs interpretation** — Agents naturally attribute intent. We built an attribution guard with 14 blocked terms and a self-correction loop.
2. **Citation fidelity** — Findings must cite exact export substrings. We reject PHANTOM_ARTIFACT when PIDs in observations don't appear in exports.
3. **Ghost vs orphan distinction** — A PID can be a ghost (not in pslist) while another PID has a live connection. We separate ghost_process from orphan_socket detection.
4. **Offline demo** — Judges may not have SIFT. We bundled synthetic Volatility exports with a known ghost PID 5678.

## Accomplishments that we're proud of

- **100% ghost/orphan recall** on sample case with **0 false positives**
- **Autonomous self-correction demo**: v1 REJECT → v2 PASS with logged rejection reasons
- **Deterministic correlate** — reproducible results, no LLM in the detection path
- **Full audit trail** in JSONL execution logs

## What we learned

- Prompt engineering alone isn't enough — exit code gates force compliance
- Substring citations are simple, auditable, and grep-friendly for judges
- Ghost-first netscan reduces noise and focuses agent attention
- The self-correction loop is the tiebreaker differentiator for FIND EVIL!

## What's next for GRAVEYARD

- malfind integration for hollow memory auto-correlation
- PPID chain analysis for ghost process ancestry
- Volatility 3 JSON output parser (in addition to text)
- Live testing against FOR508 memory samples
- GitHub Action CI running correlate + verifier on sample exports

## Built with

- Python 3
- Volatility 3
- Protocol SIFT
- Cursor / Claude
- SANS SIFT Workstation

## Links

- **GitHub:** https://github.com/let-the-dreamers-rise/graveyard
- **Demo video:** https://youtube.com/watch?v=YOUR_VIDEO_ID

## Try it out

```bash
git clone https://github.com/let-the-dreamers-rise/graveyard.git
cd graveyard
python graveyard_correlate.py --exports examples/sample_exports
python verify_findings.py examples/findings_draft_v1_reject.json --exports examples/sample_exports --json-out
python verify_findings.py examples/findings_draft_v2_pass.json --exports examples/sample_exports --report reports/report.md
```

Or on SIFT: `bash install.sh` then follow `docs/SIFT_SETUP.md`.
