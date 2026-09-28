# Testing Strategy

## Principles

1. **The suite must be hermetic.** No credentials, no network, no paid calls.
   This is what makes the tests runnable by a reviewer who has no accounts.
2. **Safety behaviour is tested explicitly.** Clinical invariants are asserted,
   not assumed.
3. **The system test asserts content, not just status codes.** A `200` with an
   empty or malformed body is a failure.
4. **Only verified results are reported.** Every number below was produced by
   running the command.

## Layers

| Layer | Tool | Scope | Count |
| --- | --- | --- | --- |
| Backend unit + HTTP | pytest + Starlette `TestClient` | `backend-v2/tests/` | 53 |
| Frontend unit | Jest + jsdom | `web-portal/src/__tests__/` | 14 |
| Type checking | `tsc --noEmit` | Whole frontend | — |
| Build | Vite | Whole frontend | — |
| System smoke | bash + curl | Live HTTP against a running API | 4 stages |
| Static checks | `make lint`, `fmt-check` | Whole repo | — |

## Hermetic setup

`backend-v2/tests/conftest.py` sets environment variables **before the
application is imported**, because `ProviderFactory` reads them at construction
time:

```python
os.environ.setdefault("AI_PROVIDER_MODE", "offline")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("GEMINI_API_KEY", "")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "100000")
```

- `offline` mode selects the deterministic provider.
- Blanking credentials prevents a developer's real keys from triggering a live,
  non-deterministic, billable call.
- `DEBUG=false` means the suite exercises the production error path.
- The raised rate limit exists because a full run exceeds 30 req/min. **The
  limiter is not disabled** — it is given headroom, and its presence is still
  asserted.

The backend root is prepended to `sys.path` so pytest works from any directory.

## Backend coverage

`test_api.py` — HTTP contract:

- **Health and discovery** — `/api/health`, `/health`, `/`, `/api/providers`
- **Validation** — empty body, missing required fields, out-of-range age,
  invalid sex, over-long and under-length symptom text
- **Analysis happy path** — response shape, urgency, explanations, confidence
  in range
- **Safety escalation** — red-flag symptoms escalate to `emergency`
- **Consent** — `consent: false` is rejected with `400`
- **Medication guarantees** — every entry is `is_educational_only: true`
- **Professional review** — `professional_review_required` is `true`
- **Image lifecycle** — upload, metadata read, preview, delete, then `404`
- **Image rejection** — disallowed MIME type, below minimum dimensions
- **Error envelope** — shape, `error_code`, and no stack-trace leakage

`test_clinical_schema.py` — schema and domain services: response serialization,
emergency classification, the educational-only medication flag, AI-generated
visual labelling, medication verification, visual education lookup, and
conversation-memory bounds and expiry.

PNG fixtures are generated in code (`make_png`) rather than committed as
binaries — self-contained, reviewable, and no extra test dependency.

## Frontend coverage

`web-portal/src/__tests__/multimodalService.test.ts` — 14 tests covering the
multimodal payload path, including the detail that `image_data_list` expects
raw base64 rather than a `data:` URL, which the backend parses differently.

Jest maps `src/services/apiClient` to a stub because the real module reads
`import.meta.env`, which Babel cannot lower to CommonJS. The stub has an
identical public surface, so application code stays free of `import.meta` and
loads under both Vite and Jest.

## System test

`./scripts/test-system.sh` starts the API if needed and runs four stages:

1. **Toolchain** — python3, node, npm, curl present; frontend deps installed
2. **Backend** — reachable, `/api/health` responds
3. **Clinical analysis** — a real `POST /api/analyze`, then structural
   validation of the response body
4. **Error handling** — `422` for an invalid body, `400` for withheld consent

Stage 3 delegates to `scripts/lib/validate_clinical_response.py`, which checks
required keys, a valid urgency value, confidence within `0.0–1.0`, a disclaimer
referencing a healthcare professional, and that every medication entry is
flagged educational-only.

The test payload is deliberately generic and non-urgent. **It never transmits
anything resembling a real patient record**, and it only terminates a backend
process that the script itself started.

> **Note on a fixed bug.** This script previously had an `if` block that was not
> closed until the end of the file, which placed the entire test body inside an
> `else` branch. On the happy path it printed one OK line, skipped every
> assertion, and exited `0` — a green result that verified nothing. It now runs
> all four stages. A test suite that can silently pass without testing anything
> is worse than no test suite.

## CI

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on push and pull
request: checkout → Python setup → install `backend-v2/requirements.txt` →
`pytest` → Node setup → `npm ci` → `tsc --noEmit` → `npm test` → `npm run build`.

**No provider credentials are used or required in CI.** There are no secrets in
the workflow file.

## Verified results

Python 3.14.6 · Node 22.23.2

```
backend-v2 $ python3 -m pytest tests/ -q
53 passed in 3.03s

web-portal $ npx jest --silent
Test Suites: 1 passed, 1 total
Tests:       14 passed, 14 total

web-portal $ npx tsc --noEmit
(0 errors)

web-portal $ npm run build
✓ 11590 modules transformed.
✓ built in 8.07s

scripts/test-system.sh
[ OK ] GET /api/health responded
[ OK ] POST /api/analyze returned a response
[ OK ] Response is a valid structured clinical document
       PASS urgency=routine confidence=0.55 explanations=1 sources=1
[ OK ] Invalid request rejected with 422
[ OK ] Missing consent rejected with 400
System test: PASSED
```

## Coverage gaps

Honest accounting of what is **not** tested:

- **No live provider tests.** Gemini and OpenAI adapters are untested against
  real APIs; their response-parsing paths are unverified.
- **No vision tests.** Nothing covers actual image interpretation.
- **No frontend component tests.** Pages and components have no render tests;
  only `multimodalService` is covered. `@testing-library/react` is installed
  but unused.
- **No load or performance tests.**
- **No security tests** for auth, authorisation, or injection.
- **No accessibility tests.**
- **No cross-browser tests.**
- **No concurrency tests** for the in-process rate limiter.
- **No tests for the prototype modules** — billing, hub, EMR, chronic care, the
  agent graph, and the mobile apps are entirely untested.

