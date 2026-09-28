# Engineering Highlights

The engineering problems this repository actually solves. Each section
describes something present in the code — not aspiration.

---

## 1. Turning a language model into a typed contract

**The problem.** A general-purpose LLM returns prose. That is unusable as an API
contract: a client cannot reliably read `urgency` from a paragraph, and a
provider swap would silently change the response shape.

**The approach.** A strict `ClinicalResponse` dataclass tree with a
deterministic `to_dict()`. Fields are guaranteed present and correctly typed:
`safety.urgency`, `possible_explanations[].evidence_level`,
`medication_information[].is_educational_only`, `sources[]`, `disclaimer`.

**Why it matters.** The system test asserts on response *content* — that a
medication entry carries the educational-only flag, that the disclaimer
references a healthcare professional. Those assertions are only possible
because the response is structured. A prose API could only be smoke-tested for
"did it return 200".

**Where.** `backend-v2/clinical_schema.py`, `backend-v2/response_transformer.py`

---

## 2. Safety as a post-processing invariant, not a prompt instruction

**The problem.** "Be careful with medical advice" in a system prompt is a
request, not a guarantee. A model that reasons badly can understate severity,
and prompt-level instructions degrade unpredictably.

**The approach.** `SafetyValidator` runs *after* the provider returns and
*before* serialization. It detects emergency red flags, urgent symptoms,
uncertainty, and prescription-like content — and it **only ever escalates**.

**The key design decision.** Escalate-only. The validator cannot lower urgency.
The model therefore cannot downgrade its own severity assessment, and the
asymmetric cost is safe: a false positive recommends unnecessary care, a false
negative is a missed emergency.

**The honest trade-off.** Escalate-only means the system will over-recommend
urgent care over time unless calibrated. Detection is keyword-based and will
miss presentations it was not written for. This is a backstop, not a triage
instrument — and the documentation says so.

**Where.** `backend-v2/safety_validator.py`

---

## 3. A provider abstraction that makes the system testable for $0

**The problem.** Code that calls a paid, rate-limited, non-deterministic API
cannot be tested hermetically. Tests become slow, flaky, and expensive, CI needs
credentials, and a reviewer with no account cannot run them at all.

**The approach.** `MultimodalAIProvider` as the contract, with three
implementations: `OfflineProvider` (deterministic rules), `GeminiProvider`, and
`OpenAIProvider`. `ProviderFactory` resolves selection once, and the orchestrator
contains no vendor logic.

**The part that makes it real.** The offline provider is not a mock — it is a
first-class implementation of the same interface, so it doubles as conformance
evidence for the abstraction. And `ProviderFactory` treats placeholder
credentials (`test-key`, `changeme`) as unusable, so a developer with a dummy
key gets a working system rather than a wall of `401`s.

**Result.** 53 backend tests that need no credentials, no network, and no
money. `./scripts/setup-and-run.sh` gets a new contributor to a working system
at $0.

**Where.** `backend-v2/providers/`

## 4. Multimodal input with a validation gate before the model

**The problem.** Image input is the easiest way to push a system into bad
behaviour: unbounded payloads, spoofed content types, undecodable files, and
images too poor to interpret.

**The approach.** Four gates before an image reaches a model:

1. **Magic-byte MIME sniffing** — the detected type wins, not the client's
   `Content-Type`. A `.exe` renamed to `.png` is rejected.
2. **Size and dimension limits** — ≤10 MB, ≥224×224, ≥1 KiB.
3. **Quality assessment** — resolution, aspect ratio, mode, and a usability
   score, with issues and warnings returned to the caller.
4. **TTL and cleanup** — 24-hour default expiry with an hourly reaper.

**Honesty as a design property.** The offline provider **explicitly refuses to
interpret images** and says so in the response's `limitations` field. The system
never implies it looked at an image when it did not.

**Where.** `backend-v2/image_service.py`, `backend-v2/providers/image_validation.py`

---

## 5. Keeping "information", "verification", and "prescribing" distinct

**The problem.** Medication content is where a health AI most easily becomes
dangerous. The difference between "ibuprofen is an NSAID" and "take 400 mg of
ibuprofen" is the difference between education and prescribing.

**The approach.** Three separate concepts, structurally separated:

- **Medication information** — served from a local reference table, every entry
  flagged `is_educational_only: true`.
- **Medication verification** — a *user-side checklist* of package items to
  confirm at a pharmacy (active ingredient, strength, expiry, regulatory mark).
- **Prescribing** — not implemented and not attempted.

**Defence in depth.** The guarantee is asserted in three independent places: a
schema test, an API test that checks every entry in a live response, and the
system-test validator. On top of that, `_contains_prescription_details()` scans
generated text for dosage patterns (`500 mg`, `3 times daily`) and drug names in
prescriptive phrasing.

**Where.** `backend-v2/medication_safety_enhanced.py`, `backend-v2/safety_validator.py`

---

## 6. Consent enforced server-side

**The problem.** A consent checkbox in the UI is not consent. It is a hint.

**The approach.** `consent: false` returns `400` **before any AI work begins**,
checked server-side at the top of the handler. The UI gate is a convenience;
the backend gate is the control.

**Current limitation, stated plainly.** Consent is a per-request boolean, not a
recorded, revocable authorization. There is no consent store, no audit of who
consented to what, and no withdrawal path. A production system would need all
three.

**Where.** `backend-v2/main_clinical.py`, `web-portal/src/pages/ConsentPage.tsx`

---

## 7. Logging that does not leak health data

**The problem.** Naive request logging on a health application writes symptom
text into log files, which then get shipped, indexed, and retained indefinitely.

**The approach.** Two distinct log paths:

- `RequestLoggingMiddleware` — method, path, client host, status, duration. No
  query strings, no bodies.
- `log_analysis_data` — request ID, session ID, age, sex, location, whether
  images were present, urgency, confidence, provider, model, latency, safety
  flags. **Metadata only.**

Never logged: free-text symptoms, conversation history, image content,
medication or allergy lists, credentials, tokens, or authorization headers.

**Also.** With `DEBUG=false`, error responses omit stack traces and internal
exception types. A test asserts a malformed request produces neither
`Traceback` nor `File "` in the response.

**Where.** `backend-v2/main_clinical.py`

## 8. Frontend error handling that cannot lie

**The problem.** A `fetch` wrapper that returns `undefined` on failure, or that
catches an error and returns an empty array, produces a UI that looks fine and
is quietly wrong. In a health application, silently showing "no possible
explanations" is worse than showing an error.

**The approach.** `apiClient` returns a discriminated `APIResult<T>`. Every
method returns `ok: true` or `ok: false`; there is no path that returns data on
failure. `OFFLINE` and `NETWORK_ERROR` are distinct codes so a write can be
queued and retried. An unparseable body yields `INVALID_JSON`, never
`undefined`. Cookies are omitted so health data does not travel via ambient
credentials.

**Where.** `web-portal/src/services/apiClient.ts`

---

## 9. Reproducible, zero-cost onboarding

**The problem.** "Clone and run" usually means: install 40 packages, obtain an
API key, configure six environment variables, and hope.

**The approach.**

- `requirements.txt` lists **only what `main_clinical` actually imports** —
  verified by importing the app in a clean virtualenv. It previously listed 40
  packages, omitted `Pillow` and `google-generativeai` (both hard imports), and
  pinned versions that no longer install.
- `./scripts/setup-and-run.sh` performs the whole flow and defaults to offline
  mode.
- `./scripts/stop.sh` kills only this checkout's processes, by PID file and by
  repository path — never a blanket `pkill -f uvicorn`, which would take down
  unrelated projects on the same machine.
- `./scripts/test-system.sh` starts the API, exercises a real request, and
  asserts on the response body.

**A bug worth naming.** `test-system.sh` had an `if` block that was never closed
until the end of the file, which put the entire test body inside an `else`. On
the happy path it printed one OK line, skipped every assertion, and exited `0`.
It reported success while testing nothing. A green test that verifies nothing is
worse than no test, and finding it is the reason the system test asserts on
content.

**Where.** `scripts/`, `Makefile`, `backend-v2/requirements.txt`

---

## 10. Documentation that matches the code

**The problem.** Health-adjacent documentation that overstates capability is a
patient-safety problem, not just a marketing one. "Clinically validated",
"HIPAA compliant", and "FDA approved" are all unverifiable claims about source
code.

**The approach.** Every capability claim in this repository maps to code, and
every gap is stated where a reader will encounter it:

- [Evidence retrieval](evidence-citation-registry.md) is documented as a *source registry*,
  not retrieval, with an explicit statement that source provenance is not
  guaranteed.
- [Multimodal](multimodal.md) is documented as *partially* implemented for
  voice, because no speech-to-text exists.
- [Security](security.md) has a section titled "What is not implemented" that is
  longer than the list of what is.
- [Testing](testing.md) ends with "Coverage gaps" listing what is untested,
  including the live provider adapters.
- The [README](../README.md) leads with a status banner and closes with medical
  limitations.

**Where.** `README.md`, `SECURITY.md`, `docs/`

---

## What is *not* an engineering highlight

Stated so this document cannot be read as more than it is:

- There is no authentication or authorization.
- There is no database, no persistence, and no durable audit log.
- There is no real evidence retrieval.
- There is no speech-to-text.
- There is no container, no cloud deployment, and no applied Kubernetes
  manifest.
- The live AI provider adapters are untested against real APIs.
- There are no frontend component tests, no performance tests, and no security
  tests.
- Nothing here is clinically validated.

The engineering value is in the **structure** — the abstraction, the typed
contract, the safety invariant, the hermetic test strategy, and the refusal to
claim more than the code supports. The clinical capability is a prototype.


