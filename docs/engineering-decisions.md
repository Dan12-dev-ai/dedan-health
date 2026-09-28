# Engineering Decisions

Architecture Decision Records for DEDAN Health. Each entry states the context,
the options considered, the decision, and its consequences — including the
consequences that are inconvenient.

---

## ADR-001 — FastAPI for the Clinical API

**Context.** The API accepts health-related text and images, validates them
strictly, applies safety rules, and returns a structured document consumed by
at least two clients (the web portal, and eventually a mobile app and a
messaging integration).

**Options considered.**
1. FastAPI + Pydantic — async, typed, OpenAPI generated from the type hints
2. Flask + manual validation — mature, synchronous, ubiquitous
3. Django + DRF — batteries included, heavier than needed for a JSON API
4. Node/Express — one language across the stack

**Decision.** FastAPI with Pydantic request models.

**Consequences.**
*Positive:* validation is declarative and colocated with the schema; the
OpenAPI document is generated rather than hand-maintained; async I/O suits
outbound provider calls; the generated docs make the API self-describing to
integrators.

*Negative:* Pydantic v2 has a learning curve, and its error format differs from
the framework's default, requiring the custom `RequestValidationError` handler
in `main_clinical.py`. The async model means blocking work (image processing)
must be handled carefully.

---

## ADR-002 — A provider abstraction instead of direct vendor calls

**Context.** Two AI providers (Gemini, OpenAI) are implemented. Vendors change
pricing, deprecate models, rate-limit, and go down. Calling a vendor SDK
directly from business logic couples the clinical pipeline to that vendor.

**Options considered.**
1. Call the vendor SDK inline in the request handler
2. A thin wrapper function per vendor
3. A `MultimodalAIProvider` interface with capability-based routing and a
   factory

**Decision.** A `MultimodalAIProvider` interface, with `ProviderFactory` handling
selection, capability routing, and fallback between providers.

**Consequences.**
*Positive:* the orchestrator contains no vendor logic; adding a provider is a
new class, not a change to the pipeline; the response shape is normalised at
the boundary, so a vendor's response-format change is contained; fallback is
configurable rather than hard-coded.

*Negative:* the interface must be broad enough for every provider, which
produces some parameters (`response_schema`, `audio`) that a given provider may
ignore. The abstraction is only as good as its conformance testing — and the
live provider adapters are currently **untested against real APIs**, which is a
real gap (see [testing.md](testing.md)).

---

## ADR-003 — A deterministic offline provider as the default

**Context.** Testing a system that calls a paid, rate-limited, non-deterministic
API is slow, flaky, and expensive. Reviewers and CI runners have no
credentials. Users in low-resource settings may have no API key or connectivity.

**Options considered.**
1. Mock at the HTTP boundary (e.g. the `responses` library)
2. Record and replay fixtures
3. A first-class provider implementing the full contract with rules-based logic
4. Require credentials and mark tests as integration-only

**Decision.** `OfflineProvider` — a real implementation of
`MultimodalAIProvider` using deterministic rules, selected by default.

**Consequences.**
*Positive:* the entire suite is hermetic and free; a new contributor can run
the system for $0; responses are reproducible, which makes assertions about
content meaningful; because the offline provider implements the *same*
interface, it doubles as conformance evidence for the abstraction.

*Negative:* the offline provider is **not a model**. Its confidence scores are
fixed constants, it does not interpret images (and says so explicitly), and its
clinical content is rules-based. There is a real risk of a user mistaking a
working offline system for a working AI system — mitigated by reporting
`provider: "offline"` and attaching an explicit safety notice to every response.

`ProviderFactory._should_use_offline()` also treats placeholder credentials
(`test-key`, `changeme`, …) as unusable, so a developer with a dummy key gets a
working system instead of a wall of `401`s.

---

## ADR-004 — Typed response models instead of free-form JSON

**Context.** A language model returns prose. Clients need predictable fields.
If the API returns whatever the model produced, every client must defend
against missing or renamed keys — and clinical safety logic would have nothing
stable to assert on.

**Options considered.**
1. Return the model's raw output
2. Return a loosely-typed dict
3. Define a strict `ClinicalResponse` schema with a deterministic serializer

**Decision.** A `ClinicalResponse` dataclass tree with an explicit `to_dict()`,
containing `safety`, `possible_explanations`, `uncertainty`,
`treatment_education`, `medication_information`, `sources`, and a mandatory
`disclaimer`.

**Consequences.**
*Positive:* the contract is explicit and versionable; clients can rely on field
names; the system test can assert on response *content*; the disclaimer cannot
be accidentally omitted, because it is a required field with a default.

*Negative:* a dataclass tree rather than Pydantic models on the response path,
chosen because the same objects are used internally by the transformer and
services. This is less integrated with FastAPI's validation and means
`/api/analyze` is declared `response_model=dict`, so **OpenAPI does not describe
the actual response shape**. That mismatch is a known weakness; the alternative
is defining parallel Pydantic response models and accepting the duplication.

## ADR-005 — Safety validation as an escalate-only post-processing stage

**Context.** A language model can understate severity. "Mild headache" in
isolation may be benign; "mild headache with chest pain" is not. If safety logic
is applied only to the model's own reasoning, a model that reasons badly
bypasses it.

**Options considered.**
1. Rely on the system prompt to make the model careful
2. Validate the final response and let the validator adjust in either direction
3. Validate and **only ever escalate**
4. Use a separate LLM call as a safety critic

**Decision.** A deterministic `SafetyValidator` that runs after the provider and
before serialization, and which **never lowers urgency**.

**Consequences.**
*Positive:* the model cannot downgrade its own severity assessment; the rules
are deterministic, auditable, and testable without a model; false positives —
the main risk of escalate-only — are safe, because the cost is an unnecessary
recommendation to seek care rather than a missed emergency.

*Negative:* escalation without de-escalation means the system will
over-recommend urgent care over time, eroding trust if it is not calibrated.
Detection is keyword-based, so it will miss presentations it was not written
for. A separate LLM critic was rejected as another non-deterministic component
in the safety path.

The prescribing detector (`_contains_prescription_details`) is a **detection**
mechanism, not a guarantee — it matches dosage patterns and drug names in
prescriptive phrasing, and can be evaded by other phrasings.

---

## ADR-006 — Evidence as a curated source registry, not live retrieval

**Context.** Responses should point users to authoritative health sources. Full
retrieval infrastructure (crawling, chunking, embedding, indexing, ranking) is
a large amount of machinery.

**Options considered.**
1. Build a retrieval pipeline now
2. Ship a curated registry of authoritative sources, clearly labelled
3. Omit sources entirely

**Decision.** A prioritised registry of authoritative sources (WHO, CDC, FDA,
NICE, MSF, PubMed, and others) that attaches citations to responses.

**Consequences.**
*Positive:* responses are directionally useful immediately; the `Source` and
`EvidenceLevel` types establish the shape real retrieval will need;
`possible_explanations` default to `evidence_level: theoretical`, so unsourced
model output is never presented as established.

*Negative — and this is the important part:* the registry does **not** fetch,
index, or quote any document. A `Source.url` is a constructed *search link*, and
`date_published` is never populated. **DEDAN does not currently guarantee source
provenance.** It is documented as citing rather than retrieving, in
[evidence-citation-registry.md](evidence-citation-registry.md), because a citation that implies
verification it does not provide is worse than no citation.

## ADR-007 — Separate frontend and backend deployments

**Context.** The portal is a React SPA; the API is a stateful service with
provider calls, image storage, and safety logic.

**Options considered.**
1. Server-render the portal from the API (single deployable)
2. Serve a built SPA from the API (single deployable, two build steps)
3. Deploy the SPA as static assets separately from the API

**Decision.** Deploy separately. In development, Vite serves the SPA on :3000
and Uvicorn serves the API on :8001.

**Consequences.**
*Positive:* the API can serve other clients — the mobile app and the messaging
backend are intended consumers of the same contract; the two scale
independently; the static bundle can be served from a CDN.

*Negative:* cross-origin requests require CORS configuration, a real source of
local-setup friction; the frontend must be configured with the API URL at build
time (`VITE_API_URL`), so a port change requires a frontend reconfiguration.
Neither the API nor the portal is containerised today.

---

## ADR-008 — Environment-based configuration via pydantic-settings

**Context.** The same code must run in development, CI, and eventually
production, in offline and live modes, with different ports, limits, and
credentials.

**Options considered.**
1. A committed config file
2. Constants in code
3. Environment variables loaded through a typed settings object
4. A secrets manager

**Decision.** A `Settings` class using `pydantic-settings`, loaded from the
environment and from `backend-v2/.env`.

**Consequences.**
*Positive:* one typed object injected where needed, which is what lets the test
suite pin `AI_PROVIDER_MODE=offline` and blank credentials for hermetic tests;
list settings accept both JSON and comma-separated values via a validator,
matching what operators actually write; `get_settings()` is `lru_cache`d so the
environment is read once.

*Negative:* `env_file = ".env"` is resolved relative to the **process working
directory**, so the API must be started from `backend-v2/` — a real source of
confusion. There is no validation that required secrets are set in production,
so a missing `ADMIN_API_KEY` falls back to a hard-coded development secret
rather than failing fast.

---

## ADR-009 — Deliberate absence of certification claims

**Context.** DEDAN is a health-related project, and there is commercial pressure
to describe it as "HIPAA compliant", "FDA approved", or "clinically validated".

**Options considered.**
1. Use the marketing language
2. Make hedged claims
3. State plainly what is and is not true

**Decision.** No certification, approval, or accuracy claim appears anywhere in
the repository. The README, SECURITY.md, and docs/security.md state explicitly
that no such certification has been obtained, and describe what *would* be
required instead.

**Consequences.**
*Positive:* the repository is honest and defensible under technical scrutiny;
a reviewer can verify every claim against the code; the medical disclaimer is
substantiated by tests rather than asserted.

*Negative:* the project reads as less mature than an overstated one, and some
readers may assume the absence of claims implies the absence of engineering
effort. This is the correct trade-off: unverifiable claims are a liability in
any due-diligence review, and in a clinical context an inflated safety claim is
a patient-safety problem.


