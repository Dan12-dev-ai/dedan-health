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
- **Evidence source registry** — prioritised authoritative sources (WHO, CDC,
  FDA, NICE, MSF, PubMed, Mayo Clinic, Cleveland Clinic).
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
- **Automated tests** — 53 backend tests (pytest) and 14 frontend tests (Jest).
- **CI** — GitHub Actions running backend tests, TypeScript type-checking, and
  the frontend build, with no provider credentials.

### Fixed

- `scripts/test-system.sh` silently skipped every assertion. An `if` statement
  opened for the health check was not closed until the end of the file, placing
  the entire test body inside the `else` branch. On the happy path the script
  reported success without running the analysis, response validation, or error
  handling checks. The branch is now closed at the point of the check and
  failures are counted.
- `backend-v2/requirements.txt` did not match the code. It omitted `Pillow` and
  `google-generativeai`, both imported at module load, and pinned obsolete
  versions of several packages. It now lists only the packages the Clinical
  API actually imports.

### Changed

- The repository was placed under version control for the first time; generated
  and runtime artifacts (virtualenvs, `node_modules`, build output, PID files,
  logs, SQLite databases, editor backups) were removed.
- Root-level planning documents were moved to `docs/planning/` to separate
  intent from current implementation.

### Known limitations

- **No authentication or authorization.** Every endpoint is public.
- **Evidence retrieval is not real retrieval.** The registry constructs
  citations to a curated source list; it does not fetch, index, or quote source
  documents, and `date_published` is never populated. See
  `docs/evidence-system.md`.
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
