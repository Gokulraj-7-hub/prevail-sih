# PREVAIL — Threat Model (of the product itself)

Status: DRAFT v0.1. PREVAIL is a security application; it must not itself become an attack surface. Checklist mirrors master prompt §28.

| Area | Risk | Mitigation | Status |
|---|---|---|---|
| Upload validation | Malicious/oversized PCAP or CSV | 200MB hard size cap (`dataset_store.MAX_UPLOAD_BYTES`), typed `IngestionError` on any parse failure instead of a crash | **Verified** — `tests/unit/test_security.py::test_oversized_upload_rejected`, `test_unparseable_upload_raises_typed_error_not_crash`. MIME/extension allowlist and a streaming parser (current parser loads the whole file via pandas) are still **Planned**. |
| Path traversal | Crafted filename in upload | Client filename is never read at all — `ingest_bytes(raw_bytes)` takes only bytes, storage path is a server-generated UUID | **Verified** — `test_stored_upload_path_is_server_generated_not_client_controlled` (asserts the function signature has no filename/path parameter to inject into). |
| Unsafe file parsing | PCAP parser crash/exploit on malformed input | Parser exceptions caught and converted to typed `IngestionError`, never propagate as a 500/crash | **Verified** at the CSV-ingestion layer (current scope — see FR-01 note below). Running the parser in a resource-limited subprocess/container boundary is still **Planned**, relevant once real PCAP (not just packet-event CSV) parsing is added. |
| Command injection | Any shell-out for tooling (e.g. capture conversion) | No shell=True with user input; use argument arrays; allowlist of invoked binaries | **Verified** by static grep (`docs/architecture/offline-verification.md`) — zero `shell=True`/`os.system` calls anywhere in `src/prevail`. |
| API authentication | Unauthenticated access if deployed beyond localhost | Local/offline deployment default; auth layer required before any non-localhost exposure — documented as a deployment precondition, not assumed | Planned — no auth layer exists; do not expose this API beyond localhost/a trusted network as currently built. |
| CORS | Overly permissive CORS on FastAPI | Explicit origin allowlist, no `*`, configurable via `PREVAIL_CORS_ORIGINS` env rather than hardcoded | **Verified** — `test_cors_default_never_wildcard`; live-tested with a real browser (Milestone 11) confirming requests from a non-allowlisted origin are blocked and an allowlisted one succeeds. |
| Secrets | Hardcoded secrets/keys | No secrets required for offline operation; `.env` gitignored; no cloud API keys in the security-critical path | Enforced. |
| Dependency vulnerabilities | Vulnerable pinned deps | Pinned versions in `pyproject.toml`/`frontend/package.json` | **Partially verified**: caught and fixed one real vulnerable pin during this build (Next.js 14.2.5 had a known CVE per `npm install`'s own warning; bumped to the patched 14.2.35, see `DECISIONS.md`-adjacent commit history). No automated `pip-audit`/`npm audit` in CI yet — **Planned**. |
| Model file integrity | Tampered model artifact loaded silently | Checksum/hash recorded in experiment manifest, verified on load | Planned — manifests record git commit/config/metrics (`common/manifest.py`) but do not yet hash-verify the model file itself before loading. |
| Pickle/joblib security | Arbitrary code execution via untrusted pickle | Never load a model file from an untrusted/uploaded source; models only loaded from the local `artifacts/` registry populated by our own training runs (`api/registry.py` hardcodes the artifacts path, never a request-derived path) | Enforced by design. |
| SSRF | Server-side request triggered by user input | No outbound network calls in the inference path at all (offline requirement covers this) | **Verified** by static grep — zero outbound HTTP/socket call patterns anywhere in `src/prevail` (`docs/architecture/offline-verification.md`). |
| Arbitrary code execution | Eval/exec on user input, unsafe deserialization | No `eval`/`exec` on request data anywhere in `src/prevail` | **Verified** by static grep — zero matches (the only `.eval()` hits are PyTorch's inference-mode toggle, inspected and confirmed unrelated to the `eval()` builtin). |
| Frontend XSS | Reflected/stored XSS in dashboard | React's default escaping, no `dangerouslySetInnerHTML` anywhere | **Verified** by grep — zero occurrences in `frontend/app`. A CSP header is still **Planned**. |
| Oversized PCAP DoS | Resource exhaustion via huge upload | Hard size cap at the API boundary | **Verified** (same test as Upload validation row). Request-level timeout middleware is still **Planned**. |
| Resource exhaustion | Rollout/what-if triggering unbounded compute | K capped server-side via pydantic `Field(ge=1, le=10)` on every request schema that takes K | **Verified** by inspection of `api/schemas.py` (`ForecastRequest.K`, `InterventionRequest.K`); FastAPI/pydantic rejects any out-of-range value before a handler runs. |

**Note on "Unsafe file parsing" scope**: the current ingestion path (`ingestion/synthetic.py` + `preprocessing/clean.py`) only parses the packet-event CSV interchange format (FR-01's "flow-CSV" path), not raw binary PCAP. Binary PCAP parsing (e.g. via `scapy`/`pyshark`) was not implemented in this pass — see `docs/limitations.md` — so the subprocess-isolation mitigation for a *binary* parser is not yet applicable and is tracked as future work alongside real-dataset integration.

## Trust boundaries

```text
[Untrusted]  uploaded PCAP/CSV  -->  [Boundary: ingestion/]  -->  [Trusted]  NetworkState objects
[Untrusted]  API request body    -->  [Boundary: api/ pydantic validation] --> [Trusted]  typed request objects
[Trusted]    local artifacts/ models  -->  loaded directly (never from upload path)
```

This document is revisited at Milestone 10 (Backend) and Milestone 12 (Hardening) once real endpoints exist to test against.
