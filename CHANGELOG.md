# Changelog

All notable changes to DEDAN Health are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

This is the first documented state of the repository. It reflects the code as
it actually exists, not a release history.

### Added

- **Clinical analysis API** — `POST /api/analyze` with a structured, typed
  clinical response (`backend-v2/main_clinical.py`).
- **AI provider abstraction** — a common `MultimodalAIProvider` contract with
  `OfflineProvider`, `GeminiProvider`, and `OpenAIProvider` implementations,
  plus a `ProviderFactory` with capability-based routing and fallback.
- **Deterministic offline provider** — rules-based analysis that requires no
  credentials, makes no network calls, and costs nothing. Selected when
  `AI_PROVIDER_MODE=offline` or when no usable provider credential is present.
- **Safety validator** — red-flag emergency escalation, urgent-symptom
  detection, uncertainty detection, prescription-detail detection, and
  disclaimer verification. Urgency is never silently downgraded.
- **Clinical response schema** — a typed `ClinicalResponse` tree with a
  deterministic serializer, including explicit uncertainty statements and
  evidence levels.
- **Image pipeline** — multipart and base64 upload, magic-byte MIME sniffing,
  quality gating (≥224×224, ≥1 KiB, aspect-ratio warnings), configurable TTL,
  and periodic expiry cleanup.
- **Medication safety service** — educational medication information, pharmacy
  package-verification workflow, and questions to ask a pharmacist. Every entry
  is flagged `is_educational_only`.
- **Evidence citation registry** — a prioritised list of authoritative sources
  (WHO, CDC, FDA, NICE, MSF, PubMed, Mayo Clinic, Cleveland Clinic) with
  citations attached to responses. **Not a retrieval system** — see "Known
  limitations".
- **Multimodal orchestrator** — modality detection, clinical context assembly,
  provider selection, safety validation, and audit logging.
- **Web portal** — React 18 + TypeScript + Vite assessment flow, results view,
  consent page, history, design-system tokens, and a typed API client.
- **Operational middleware** — per-IP rate limiting, CORS allow-list, request
  timing/logging, session middleware, and `TrustedHostMiddleware` in production.
- **Structured error envelope** — a single `{error, error_code, details,
  timestamp}` shape across all error paths, with stack-trace suppression when
  `DEBUG=false`.
- **Developer tooling** — `Makefile`, `scripts/setup-and-run.sh`,
  `scripts/stop.sh`, `scripts/health-check.sh`, `scripts/test-system.sh`,
  `scripts/check-format.sh`.
- **Automated tests** — 53 backend tests (pytest) and 25 frontend tests (Jest),
  including component tests for the safety-critical `SeverityBadge` and the
  `ProgressIndicator` / `AssessmentShell` workflow components.
- **CI** — GitHub Actions running backend tests, TypeScript type-checking, the
  frontend build, and shell syntax checks, with no provider credentials.

### Documentation

- `docs/security.md`, `docs/api.md`, and the README now carry an explicit
  **⛔ production-blocker notice** stating that the API has no authentication or
  authorization and that `ADMIN_API_KEY` authenticates nothing.
- `docs/ai-providers.md` documents provider selection, the credential-free mock
  mode, and why real-provider tests are excluded from CI.
- `data/clinical_guidelines/PROVENANCE.md` records the provenance status of the
  guideline JSON files, which are excluded from the repository licence.
- `docs/evidence-system.md` was renamed to
  `docs/evidence-citation-registry.md` so the filename matches what the code
  does.

### Fixed

- `scripts/test-system.sh` silently skipped every assertion. An `if` statement
  opened for the health check was not closed until the end of the file, placing
  the entire test body inside the `else` branch. On the happy path the script
  reported success without running the analysis, response validation, or error
  handling checks. The branch is now closed at the point of the check and
  failures are counted.
- `backend-v2/requirements.txt` did not match the code. It omitted `Pillow`,
  `google-generativeai`, `itsdangerous`, and `numpy`, all of which are imported
  at module load, and pinned obsolete versions of several packages. The first
  CI run on GitHub Actions failed on the missing `itsdangerous` before this was
  caught. The file now lists only the packages the Clinical API actually
  imports, verified in a clean virtualenv.
- `@testing-library/jest-dom` was a devDependency but was never registered via
  `setupFilesAfterEnv`, so no DOM matcher existed and no component test could be
  written. Added `web-portal/jest.setup.ts`.

### Changed

- The repository was placed under version control for the first time; generated
  and runtime artifacts (virtualenvs, `node_modules`, build output, PID files,
  logs, SQLite databases, editor backups) were removed.
- Root-level planning documents were moved to `docs/planning/` to separate
  intent from current implementation.

### Known limitations

- **⛔ No authentication or authorization.** Every endpoint is public. This is a
  production blocker, documented as such in the README, `docs/security.md`, and
  `docs/api.md`.
- **Evidence is a citation registry, not retrieval.**
  `evidence_retrieval_enhanced.py` contains no HTTP client and performs no
  network requests. It does not fetch, index, or quote source documents, and
  `date_published` is never populated. Nothing in a response has been checked
  against the source it cites. See `docs/evidence-citation-registry.md`.
- **Copyright holder and data provenance are unresolved.** The `LICENSE`
  copyright line is a placeholder, and `data/clinical_guidelines/` is excluded
  from the licence because its redistribution rights are unconfirmed. Those
  files are not used by the verified Clinical API.
- **No speech-to-text.** The voice modality accepts a client-supplied
  transcript; the backend never decodes audio.
- **Offline mode cannot interpret images.** The offline provider explicitly
  declines to perform computer vision and says so in the response.
- **Red-flag detection is keyword-based.** It will miss presentations it was
  not written for. It is a backstop, not a clinical triage instrument.
- **The audit log is not durable.** Entries go to the application log and are
  not persisted to a tamper-evident store.
- **In-memory state.** The rate limiter, image metadata index, and conversation
  memory are process-local and do not survive a restart or scale horizontally.
- **Live AI providers are untested.** No test calls Gemini or OpenAI, so their
  response-parsing paths are unverified. This is deliberate — see
  `docs/ai-providers.md`.
- **Not clinically validated.** No prospective study, outcome evaluation, or
  regulatory review has been performed.
- **Prototype code is retained but unwired.** `backend-v2/agents/` (LangChain +
  CrewAI), `billing_*`, `chronic_care.py`, `hub_system.py`, `emr_connector.py`,
  `messaging-backend/`, `clinic-dashboard/`, `mobile-app/`, and `kubernetes/`
  are present but are not part of the verified system.
- **Legacy duplicates.** Several modules exist in both an original and an
  `_enhanced` form (for example `evidence_retrieval.py` and
  `evidence_retrieval_enhanced.py`); only the latter is used by the Clinical
  API.
