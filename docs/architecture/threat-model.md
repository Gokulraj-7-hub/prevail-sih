# PREVAIL — Threat Model (of the product itself)

Status: DRAFT v0.1. PREVAIL is a security application; it must not itself become an attack surface. Checklist mirrors master prompt §28.

| Area | Risk | Mitigation | Status |
|---|---|---|---|
| Upload validation | Malicious/oversized PCAP or CSV | Enforce MIME/extension allowlist, max size, streaming parse with hard timeout, quarantine dir | Planned — `ingestion/` |
| Path traversal | Crafted filename in upload | Never use client-supplied filename directly; server-generated UUID storage path | Planned — `api/` |
| Unsafe file parsing | PCAP parser crash/exploit on malformed input | Run parsing in a resource-limited subprocess/container boundary where feasible; treat parser exceptions as typed `IngestionError`, never crash the API process | Planned |
| Command injection | Any shell-out for tooling (e.g. capture conversion) | No shell=True with user input; use argument arrays; allowlist of invoked binaries | Enforced by code review checklist |
| API authentication | Unauthenticated access if deployed beyond localhost | Local/offline deployment default; auth layer required before any non-localhost exposure — documented as a deployment precondition, not assumed | Planned |
| CORS | Overly permissive CORS on FastAPI | Explicit origin allowlist, no `*` in non-dev config | Planned |
| Secrets | Hardcoded secrets/keys | No secrets required for offline operation; `.env` gitignored; no cloud API keys in the security-critical path | Enforced |
| Dependency vulnerabilities | Vulnerable pinned deps | `pip-audit`/`npm audit` in CI (or documented manual run), pinned versions in `pyproject.toml`/`package.json` | Planned |
| Model file integrity | Tampered model artifact loaded silently | Checksum/hash recorded in experiment manifest, verified on load | Planned |
| Pickle/joblib security | Arbitrary code execution via untrusted pickle | Never load a model file from an untrusted/uploaded source; models only loaded from the local `artifacts/` registry populated by our own training runs; prefer `safetensors`/plain-JSON weights where practical for the small models used here | Enforced by design |
| SSRF | Server-side request triggered by user input | No outbound network calls in the inference path at all (offline requirement covers this) | Enforced by design |
| Arbitrary code execution | Eval/exec on user input, unsafe deserialization | No `eval`/`exec` on request data anywhere in `src/prevail` | Enforced by code review checklist |
| Frontend XSS | Reflected/stored XSS in dashboard | React's default escaping, no `dangerouslySetInnerHTML` on server-derived strings without sanitization, CSP header | Planned — `frontend/` |
| Oversized PCAP DoS | Resource exhaustion via huge upload | Hard size cap + streaming + request timeout at the API boundary | Planned |
| Resource exhaustion | Rollout/what-if triggering unbounded compute | K capped server-side (matches evaluated K ∈ {1,2,3,5}), request-level timeout | Planned |

## Trust boundaries

```text
[Untrusted]  uploaded PCAP/CSV  -->  [Boundary: ingestion/]  -->  [Trusted]  NetworkState objects
[Untrusted]  API request body    -->  [Boundary: api/ pydantic validation] --> [Trusted]  typed request objects
[Trusted]    local artifacts/ models  -->  loaded directly (never from upload path)
```

This document is revisited at Milestone 10 (Backend) and Milestone 12 (Hardening) once real endpoints exist to test against.
