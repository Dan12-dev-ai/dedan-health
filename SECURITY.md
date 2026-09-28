# Security Policy

## Scope

DEDAN Health processes **health-related information submitted voluntarily by
users** — symptom descriptions, age, sex, medications, allergies, and
optionally images. That makes this a sensitive-data application even in its
current prototype state.

This document covers how to report a vulnerability and what protections exist
today. For the engineering-level detail (threats, controls, and what a
production deployment still requires), see [docs/security.md](docs/security.md).

## Reporting a Vulnerability

Please report suspected vulnerabilities privately rather than opening a public
issue. Use GitHub's **"Report a vulnerability"** private advisory form on this
repository, or open a private security advisory.

Please include:

- A description of the issue and its impact
- Steps to reproduce, or a proof of concept
- The commit SHA or version affected
- Whether any real health data was involved

**Do not include real patient information in a report.** Use synthetic data.

There is no formal SLA. If you do not receive an acknowledgement, follow up
after a reasonable period.

## Security Posture Today

DEDAN Health is a **prototype**. The protections listed below are real and
tested; the gaps listed below are real and documented.

### Implemented

| Control | Where |
| --- | --- |
| Secrets excluded from version control | `.gitignore` (`.env`, `.env.*`, with `*.example` tracked) |
| No credentials in the repository or history | Verified by repository-wide secret scan |
| Input validation on all request bodies | Pydantic models in `backend-v2/models/` |
| Upload validation (magic bytes, size, dimensions) | `backend-v2/image_service.py` |
| Filename sanitisation on upload | `image_service._sanitize_filename` |
| Rate limiting per client IP | `RateLimitMiddleware` in `main_clinical.py` |
| CORS allow-list | `CORS_ORIGINS` setting |
| Stack-trace suppression in error responses | Exception handlers; `DEBUG=false` |
| Interactive API docs disabled when `DEBUG=false` | `create_app()` |
| Consent gate before any AI processing | `POST /api/analyze` |
| Automatic expiry of uploaded images | `IMAGE_TTL_HOURS` + periodic cleanup task |
| Logging excludes credentials and free-text symptoms | `log_analysis_data()` records metadata only |

### Not Implemented

These are **absent**, not merely undocumented. Do not expose this service to an
untrusted network until they are addressed:

- **Authentication and authorization** — every endpoint is public.
- **Encryption in transit** — no TLS termination in-repo (expected at a proxy).
- **Encryption at rest** — uploaded images are stored as plain files.
- **Durable audit logging** — audit entries go to the application log only.
- **Key management or rotation** — provider keys are read from the environment.
- **Dependency and container scanning** in CI.
- **Data-retention automation** beyond image TTL.
- **Consent storage and revocation** — consent is a per-request boolean, not a
  recorded, revocable authorization.
- **Multi-tenant isolation.**

## Reporting a Safety Issue

A clinical-safety defect (for example, a red-flag symptom that fails to
escalate, or medication content that reads as prescribing) is a
**security-relevant bug** even though it is not an exploit. Please report it
using the same private channel, and label it clearly as a safety issue.

## Responsible Disclosure

We ask that you:

- Avoid accessing or retaining real patient data while testing
- Avoid sending traffic that degrades service for other users
- Give us a reasonable window to ship a fix before public disclosure
- Do not publicly claim a compliance certification that this project does not
  hold

## Compliance

DEDAN Health is **not** HIPAA, GDPR, FDA, WHO, or SOC 2 certified, and no such
claim is made anywhere in this repository. See
[docs/security.md](docs/security.md) for the specific controls that would be
required before a production healthcare deployment.
