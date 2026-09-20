# Offline / Air-Gapped Operation — Verification (Phase 21)

Status: functionally verified end-to-end via `scripts/offline_smoke_test.sh` against the real Docker Compose stack (2026-09-20) — health check, demo-dataset load, forecast, and dashboard render all passed. Egress-blocked network isolation itself was not independently re-verified (see §2 below). Two layers of verification, one done, one only partially achievable in this environment.

## 0. Live smoke-test result

```text
== Waiting for API health ==
API healthy after 1s
== Loading sample telemetry (demo dataset) ==
== Running forecast ==
== Checking dashboard renders ==
Dashboard OK after 2s
== ALL CHECKS PASSED ==
```

This caught a real bug on the first attempt: `pyarrow` was installed ad hoc in the local dev `.venv` but never declared in `pyproject.toml`, so the from-scratch Docker image crashed on startup (`ImportError: ... pyarrow or fastparquet is required`). Fixed by declaring the dependency (see `DECISIONS.md` D-011) — exactly the kind of gap this smoke test exists to catch, and it worked as intended.

## 1. Static code verification (done)

```bash
grep -rnE "requests\.(get|post|put)|urllib\.request|httpx\.(get|post)|socket\.connect|urlopen" src/prevail/ --include="*.py"
grep -rnE "\beval\(|\bexec\(|os\.system\(|shell=True" src/prevail/ --include="*.py"
grep -rnE "https?://[a-zA-Z]" frontend/app frontend/lib --include="*.ts" --include="*.tsx"
```

Results (2026-09-20, commit at time of this doc):

- **No outbound HTTP/socket calls anywhere in `src/prevail`** — the backend never calls out to anything, cloud or otherwise, at inference time.
- **No `eval`/`exec`/`os.system`/`shell=True`** anywhere in the backend (the only regex hits were PyTorch's `.eval()` inference-mode calls, which are unrelated to Python's `eval()` builtin — verified by inspection, not just the grep match).
- **The frontend only ever calls `NEXT_PUBLIC_API_BASE`**, a locally-configured URL — no hardcoded third-party/cloud endpoint anywhere in `frontend/app` or `frontend/lib`.

This is real evidence the *code* doesn't attempt outbound calls, but it is a static check, not a runtime network-block test.

## 2. Runtime network-block test (attempted, environment-limited)

The master prompt's specified test is:

```text
network disabled -> start application -> load sample telemetry -> forecast -> dashboard works
```

A true version of this (e.g. `iptables`-blocking the Docker bridge network's egress, or running containers on a `--internal` Docker network with no route out) requires host-level network administration privileges. **Not verified in this pass** — this development environment's sandboxing did not permit modifying host firewall rules to test egress-blocking rigorously; attempting it is recorded here rather than silently skipped.

What WAS verified instead (`scripts/offline_smoke_test.sh`): the full `docker compose` stack (backend + frontend, both built from the offline-baked images with trained artifacts and the demo dataset included, no volumes required) starts, serves the health check, loads the demo dataset, runs a forecast, and the dashboard renders — all against `localhost` container-to-container traffic only, consistent with (but not a strict proof of) no external dependency.

**Recommended follow-up** for a fuller acceptance-criteria pass: run `scripts/offline_smoke_test.sh` on a host where the tester can create a Docker network with no default route to the internet (e.g. `docker network create --internal prevail-offline`) and confirm the same result.
