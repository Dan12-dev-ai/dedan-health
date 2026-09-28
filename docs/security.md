# Security

> ## ⛔ PRODUCTION BLOCKER — no authentication
>
> **The DEDAN Health API has no authentication or authorization. Every endpoint
> is public.** Anyone who can reach the network path can submit an analysis
> request, upload images, read them back, and delete them.
>
> Verified by inspection: `backend-v2/main_clinical.py` contains no
> `APIKeyHeader`, no `OAuth2PasswordBearer`, no auth dependency, and no
> `Depends` guard other than internal service accessors. `ADMIN_API_KEY` exists
> in settings but is used **only** as the `SessionMiddleware` signing secret —
> it authenticates nothing.
>
> **Do not expose this service to any untrusted network, and do not handle real
> patient data with it, until authentication and per-patient authorization are
> implemented.** This is a prototype limitation, not a configuration choice.
>
> What that work would entail is described under
> [Before production healthcare deployment](#before-production-healthcare-deployment).
> It has deliberately **not** been implemented here, because a partial
> authentication system is worse than a clearly absent one.

This document describes the security model of DEDAN Health as it exists, and
what would be required before production use in a healthcare setting.

For vulnerability reporting, see [../SECURITY.md](../SECURITY.md).

## Threat model

DEDAN accepts **voluntarily submitted health information** — symptom
descriptions, age, sex, medications, allergies, and optionally photographs.
That makes it sensitive-data infrastructure even in prototype form, and it makes
three parties relevant:

| Party | Concern |
| --- | --- |
| User | Their health data and images are disclosed, stored, and sent to a third-party AI provider |
| Operator | Breach exposure, liability for incorrect clinical guidance, regulatory exposure |
| AI provider | Receives identifiable health text and images as a third party |

## Controls that exist

### Secrets management

- `.gitignore` excludes `.env`, `.env.*`, and all of `venv/`, `.venv/`,
  `node_modules/`; `*.example` templates are explicitly re-included.
- Provider credentials are read from the environment via `pydantic-settings`
  and are never written to disk, logged, or returned in a response.
- `ProviderFactory` refuses to treat placeholder values as usable, which
  prevents accidental live calls with dummy keys.

A repository-wide scan for credential patterns (`sk-…`, `AIza…`, `AKIA…`,
`-----BEGIN … PRIVATE KEY-----`) returns no matches, and no `.env` file is
tracked.

### Input validation

- All request bodies are validated by Pydantic before any processing.
- `patient_age` is bounded to `0–150`; `patient_sex` is a `Literal`;
  `symptom_description` is bounded to 10–3000 characters.
- Uploads are validated by **magic bytes** rather than the client-supplied
  `Content-Type`, against an allow-list of four image formats.
- File size, minimum dimensions, and a corruption floor are checked before
  storage.
- Filenames are reduced to `[A-Za-z0-9._-]` and truncated, preventing path
  traversal via the stored name.
- Stored files use generated UUID filenames, never the client's.

### API security

- Per-IP rate limiting (30 req/min default) on all non-exempt paths.
- CORS restricted to a configurable allow-list.
- `TrustedHostMiddleware` enabled when `ENVIRONMENT=production`.
- Interactive docs disabled unless `DEBUG=true`.
- Session cookies are `https_only` in production.

### Error handling

A single error envelope is used for every failure path. With `DEBUG=false`,
stack traces are never returned, internal exception type names are not
disclosed, and `details` is `null` for unhandled errors. A test asserts that a
malformed request body produces neither `Traceback` nor `File "` in the
response.

### Logging and sensitive data

`log_analysis_data` records **metadata only**: request ID, session ID, age,
sex, location, whether images were present, urgency, confidence, provider,
model, latency, and safety flags. It does **not** record free-text symptoms,
conversation history, image content, credentials, tokens, authorization
headers, medication lists, or allergy lists.

Request logging captures method, path, client host, status, and duration — not
query strings or bodies.

### Data retention

Uploaded images expire after `IMAGE_TTL_HOURS` (default 24) and a background
task reclaims them hourly. Images can be deleted on demand.

**Limitation:** retention is in-process only. The metadata index is a Python
dict; a restart orphans files on disk with no metadata to reclaim them.

## What is not implemented

**This is the more important half of the document.**

| Gap | Consequence |
| --- | --- |
| **No authentication** | Every endpoint, including image upload and analysis, is public |
| **No authorization** | No concept of user, role, or per-patient scoping |
| **No encryption in transit** | No TLS in-repo; expected at a terminating proxy |
| **No encryption at rest** | Uploaded images are plain files under `IMAGE_STORAGE_PATH` |
| **No durable audit log** | Audit entries go to stdout; not tamper-evident or queryable |
| **No key rotation** | Keys are long-lived environment variables |
| **No consent storage** | Consent is a per-request boolean, not a recorded, revocable authorization |
| **No data deletion workflow** | No record deletion; no subject-access support |
| **No secrets manager** | Keys live in the process environment |
| **No dependency scanning in CI** | Vulnerable transitive dependencies would not be caught |
| **In-process rate limiting** | Trivially bypassed across restarts and replicas |
| **`X-Forwarded-For` trusted blindly** | Correct only behind a proxy that overwrites the header |
| **No CSP or security headers** on the portal | No CSP, HSTS, or `X-Frame-Options` |

## Before production healthcare deployment

None of the following is currently satisfied. This is a checklist of what would
be required, not a claim of compliance.

**Legal and regulatory**

- Determine applicable regimes (HIPAA, GDPR, UK GDPR, Kenya Data Protection
  Act, and so on) and obtain counsel.
- Execute BAAs / DPAs with every AI provider that will receive health data.
- Assess whether the software is a regulated medical device in the target
  jurisdiction, and obtain the required clearance or exemption.
- Establish consent capture, withdrawal, and retention policy.
- Provide a data-subject access and deletion path.

**Technical**

- Implement authentication and per-patient authorization.
- Terminate TLS; encrypt storage for images and any persisted records.
- Replace the in-process rate limiter with a shared store.
- Move the audit log to durable, append-only storage with integrity protection.
- Integrate a secrets manager with automated rotation.
- Add dependency and container scanning to CI.
- Add CSP and security headers to the frontend.
- Minimise and encrypt anything forwarded to a third-party provider, and give
  users a genuine choice about it.

**Clinical governance**

- Prospective clinical validation against a defined reference standard.
- Clinician review of the safety rules, red-flag list, and medication content.
- A defined update process for clinical content, with an owner and a cadence.
- Adverse-event reporting and a route for users to flag unsafe output.
- Ongoing monitoring of escalation accuracy and false-negative rates.

## No certification claims

DEDAN Health is **not** certified or approved by HIPAA, GDPR, FDA, WHO, or SOC
2, and no such claim appears anywhere in this repository. Certifications apply
to an organisation's practices and controls, not to source code, and none have
been obtained.

