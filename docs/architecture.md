# Architecture

This document describes **what is actually implemented** in this repository and
why the components are separated. It deliberately does not describe the
prototype directories as if they were part of the running system.

## 1. System Overview

DEDAN Health is a two-tier application:

- A **React single-page application** (`web-portal/`) that collects a
  patient-described problem and renders a structured result.
- A **FastAPI service** (`backend-v2/`) that validates the request, orchestrates
  an AI provider, applies safety rules, and returns a typed clinical document.

They communicate over JSON/HTTP. The full request path is in
[`diagrams/request-flow.mmd`](diagrams/request-flow.mmd); the component view is
in [`diagrams/architecture.mmd`](diagrams/architecture.mmd).

## 2. Verified System Components

### Frontend — `web-portal/`

| Component | Responsibility |
| --- | --- |
| `src/pages/` | Assessment flow, results, history, consent, settings, help |
| `src/components/assessment/` | Multimodal input (text, image attachment, voice recorder) |
| `src/services/apiClient.ts` | Typed `fetch` wrapper returning `APIResult<T>` |
| `src/services/multimodalService.ts` | Image encoding and multimodal payload assembly |
| `src/design-system/` | Design tokens, `SeverityBadge`, `TrustBanner`, form primitives |
| `src/state/DedanContext.tsx` | Application state container |
| `src/__tests__/` | Jest suite |

### Backend — `backend-v2/`

| Module | Responsibility |
| --- | --- |
| `main_clinical.py` | App factory, middleware, error handlers, route handlers |
| `app/core/config.py` | Environment-driven `Settings` (pydantic-settings) |
| `models/models.py` | Pydantic request/response contracts |
| `clinical_schema.py` | `ClinicalResponse` schema and deterministic serializer |
| `providers/models.py` | Provider-agnostic contracts and capability model |
| `providers/provider_factory.py` | Provider selection, fallback, health checks |
| `providers/orchestrator.py` | Modality detection, context assembly, orchestration |
| `providers/offline_provider.py` | Deterministic rules-based provider |
| `providers/gemini_provider.py` | Google Gemini adapter |
| `providers/openai_provider.py` | OpenAI adapter |
| `providers/image_validation.py` | Image quality assessment |
| `safety_validator.py` | Escalation-only safety rules |
| `image_service.py` | Upload, validation, TTL storage, cleanup |
| `clinical_context_builder.py` | Normalised clinical context |
| `response_transformer.py` | Provider output → `ClinicalResponse` |
| `medication_safety_enhanced.py` | Educational medication information |
| `evidence_retrieval_enhanced.py` | Authoritative source registry |
| `visual_education_enhanced.py` | Educational visual references |
| `conversation_memory.py` | Bounded per-session conversation history |
| `urgency_engine.py` | Urgency classification helpers |
| `tests/` | pytest suite (53 tests) |

## 3. Why the Components Are Separated

**Provider abstraction from orchestration.**
`MultimodalOrchestrator` depends on the `MultimodalAIProvider` contract, not on
Gemini or OpenAI. This is what allows the entire test suite to run offline and
deterministically. Vendor selection is resolved once, in `ProviderFactory`,
rather than scattered through business logic.

**Safety validation as a distinct stage.**
Safety rules are applied *after* the model returns and *before* the response is
serialized. Inline in the route handler they would be easy to bypass on a new
code path. As a separate stage with an escalate-only contract, the invariant
"urgency is never downgraded" is enforced in one place.

**Response schema separate from provider output.**
Providers return a loosely-shaped `AnalysisResponse`; the application emits a
strictly-shaped `ClinicalResponse`. The transformer is the only module that
knows both, so a provider change cannot silently alter the public API contract.

**Environment-driven configuration.**
`Settings` is injected rather than read from globals, which is what allows the
test suite to pin `AI_PROVIDER_MODE=offline` and blank out credentials, making
the suite hermetic.

**Frontend/backend separation.**
The portal is a static asset bundle and the API is a stateful service. Keeping
them separate allows independent scaling and lets the API serve other clients —
the mobile app and messaging backend are intended future consumers of the same
contract.

## 4. Request Lifecycle

`POST /api/analyze` proceeds as follows:

1. **Rate limiting** — `RateLimitMiddleware` applies a per-client-IP sliding
   window. Health and docs paths are exempt.
2. **Validation** — `AnalyzeRequest` is parsed by Pydantic. Failures produce a
   `422` with the standard error envelope.
3. **Consent gate** — `consent: false` produces a `400` before any AI work.
4. **Input assembly** — text, duration, severity, voice transcript, and
   conversation history are combined; `image_ids` are resolved and base64
   images decoded.
5. **Provider invocation** — the orchestrator selects a provider and calls it.
6. **Safety validation** — `validate_async` then `apply_safety_result_async`.
7. **Context build and transform** — a normalised clinical context is built and
   converted to a `ClinicalResponse`.
8. **Enrichment** — education and medication-verification content are attached.
9. **Serialization** — `ClinicalResponse.to_dict()` produces the response.
10. **Audit log** — a background task records request ID, session, urgency,
    confidence, provider, latency, and safety flags.

## 5. Cross-Cutting Concerns

### Error handling

All error paths return one envelope:

```json
{
  "error": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "details": [],
  "timestamp": 1750000000.0
}
```

`HTTPException` → `HTTP_<status>`; validation failures → `VALIDATION_ERROR`;
unhandled exceptions → `INTERNAL_ERROR`, with the exception type included
**only** when `DEBUG=true`. Stack traces are never returned to the client.

### Observability

`RequestLoggingMiddleware` logs method, path, client host, status, and duration,
and sets an `X-Process-Time` response header. `log_analysis_data` writes an
`AUDIT:` entry containing **metadata only** — never free-text symptoms,
credentials, or image content. There is no metrics exporter, tracing, or
structured log sink; the format is a JSON-ish line emitted by `logging`.

### Statefulness

The rate-limit window, image metadata index, and conversation memory are all
**in-process**. Restarting the API clears them, and running multiple replicas
gives inconsistent behaviour. There is no database on the verified path.

## 6. Prototype and Legacy Code

The following exist in the repository but are **not** part of the verified
system. They are not imported by `main_clinical.py`, are not covered by the
test suite, and are not documented as working.

| Path | Status |
| --- | --- |
| `backend/` | Earlier FastAPI backend (v1). Superseded by `backend-v2/`. Contains a Dockerfile that has not been verified. |
| `backend-v2/agents/` | LangChain + CrewAI agent graph. Requires deprecated `langchain` 0.x. Not imported by the Clinical API. |
| `backend-v2/main_v2.py` | Larger experimental API surface. Not the running app. |
| `backend-v2/{billing,chronic_care,hub_system,emr_connector,risk_sentinel,database_security,safety_bias_layer}.py` | Capability modules. Present but unwired. |
| `backend-v2/*.py` vs `*_enhanced.py` | Duplicate pairs (for example `evidence_retrieval.py` and `evidence_retrieval_enhanced.py`). Only the `_enhanced` variants are used by the Clinical API. |
| `messaging-backend/` | WhatsApp/Twilio integration. Unverified. |
| `clinic-dashboard/` | React clinician console (CRA). Unverified. |
| `mobile-app/` | React Native app. Unverified. |
| `mobile/`, `web/` | Thin API-client shells. Unverified. |
| `kubernetes/` | Manifests. Never applied to a cluster. |
| `docs/planning/` | Historical planning documents. Intent, not implementation. |

These were retained rather than deleted so the project's history stays visible.
The recommended path is to quarantine or remove them — see the roadmap in the
[README](../README.md).

## 7. Future Architecture (not implemented)

The following would be required for a production deployment. None of it exists
today.

- **Persistence layer** — a real database for sessions, consent records, and an
  append-only audit log.
- **Shared rate limiting and caching** — Redis, so limits survive restarts and
  apply across replicas.
- **Authentication and authorization** — identity, role-based access, and
  per-patient scoping.
- **Real evidence retrieval** — indexing authoritative sources, retrieving
  passages, and quoting them with provenance and staleness handling.
- **Server-side speech-to-text** — decoding audio rather than accepting a
  client transcript.
- **Horizontal scaling** — externalising all in-process state.
- **Containerisation and orchestration** — Docker images and validated
  Kubernetes manifests.

