# SIFT Workstation Setup for GRAVEYARD

Step-by-step guide to run GRAVEYARD on SANS SIFT Workstation (OVA or ISO).

## Prerequisites

- SANS SIFT Workstation VM (Ubuntu-based)
- 8 GB+ RAM allocated to VM
- Windows memory image (`.raw` / `.vmem` / `.dmp`)
- Cursor IDE (optional, for agent-driven triage)

## Option A: SIFT OVA (recommended)

### 1. Download and import

1. Download SIFT OVA from [SANS SIFT page](https://www.sans.org/tools/sift-workstation/)
2. Import into VirtualBox or VMware
3. Boot and login (default credentials per SANS documentation)
4. Update packages: `sudo apt update && sudo apt upgrade -y`

### 2. Verify Volatility 3

```bash
vol.py -h | head -5
# Expected: Volatility 3 Framework
```

If missing: `pip3 install volatility3`

### 3. Install Protocol SIFT + GRAVEYARD

```bash
git clone https://github.com/YOUR_USERNAME/graveyard.git
cd graveyard
bash install.sh
```

This installs Protocol SIFT (if absent) and sets up `/cases/graveyard/` workspace.

### 4. Copy memory image

```bash
sudo mkdir -p /cases/graveyard/evidence
sudo cp /path/to/mem.raw /cases/graveyard/evidence/
sudo chown -R $(whoami) /cases/graveyard
```

**Never modify the original evidence file.**

## Option B: Protocol SIFT install only (existing SIFT)

If SIFT is already running with Protocol SIFT:

```bash
export GRAVEYARD_DIR=/path/to/graveyard
export CASE_ROOT=/cases/graveyard
bash install.sh
```

## Live triage workflow

```bash
cd /cases/graveyard
bash /path/to/graveyard/scripts/run_live_triage.sh /cases/graveyard/evidence/mem.raw /cases/graveyard
```

Or use the manual steps in the "Live triage workflow" section above.

## Cursor agent setup

1. Open `/cases/graveyard` in Cursor
2. Ensure `AGENTS.md` is in workspace root
3. `.cursor/rules/graveyard.mdc` applies automatically
4. Prompt agent: "Run GRAVEYARD memory triage on mem.raw following AGENTS.md"

## Offline test (no VM required)

```bash
python3 graveyard_correlate.py --exports examples/sample_exports
python3 verify_findings.py examples/findings_draft_v2_pass.json --exports examples/sample_exports --report reports/report.md
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `vol.py: command not found` | `pip3 install volatility3` or use `python3 -m volatility3` |
| Symbol errors | Run `vol.py -f IMAGE windows.info` first; may need symbol download |
| Permission denied on /cases | `sudo chown -R $(whoami) /cases/graveyard` |
| Verifier CITATION_MISMATCH | Ensure matched_text is exact substring from export file |
| No ghosts found | Normal for clean memory — sample exports demonstrate ghost case |

## Parallel SIFT note

This setup satisfies the hackathon SIFT requirement. For judges without VM access, bundled `docs/demo/exports/` provides identical sample data.
