# AI Provider Configuration

This document covers how a provider is selected, how **mock mode** works
without any credentials, and why real-provider tests are excluded from normal
CI.

- Source: `backend-v2/providers/`
- Selection logic: `providers/provider_factory.py`
- Interface: `providers/models.py`

## The three providers

| Provider | Module | Credentials | Cost | In CI |
| --- | --- | --- | --- | --- |
| `offline` | `offline_provider.py` | None | $0 | **Yes** |
| `gemini` | `gemini_provider.py` | `GEMINI_API_KEY` | Usage-billed | No |
| `openai` | `openai_provider.py` | `OPENAI_API_KEY` | Usage-billed | No |

All three implement the same `MultimodalAIProvider` contract, so the
orchestrator never branches on vendor.

## Mock mode requires no credentials

**Verified behaviour.** With `GEMINI_API_KEY`, `OPENAI_API_KEY`, and
`AI_PROVIDER_MODE` all unset, the system selects `OfflineProvider` and serves a
complete, structured response:

```
$ env -u GEMINI_API_KEY -u OPENAI_API_KEY -u AI_PROVIDER_MODE \
    python -c "...POST /api/analyze..."
HTTP: 200
provider: offline
urgency: routine
resolved provider: OfflineProvider
```

This works because `ProviderFactory._should_use_offline()` returns `True` when
**either** offline mode is requested **or** no *usable* credential is present.
"Usable" is decided by `_has_usable_credential()`, which rejects any key
containing `test-key`, `test_key`, `your-`, `your_`, `changeme`, `placeholder`,
`xxx`, `<api`, `dummy`, or `example`.

The practical effect: a contributor who clones the repository, runs
`./scripts/setup-and-run.sh`, and has a stale or placeholder key in their shell
still gets a working system instead of a wall of `401`s.

## Selecting a mode

| Intent | Configuration |
| --- | --- |
| Free, deterministic, no credentials | `AI_PROVIDER_MODE=offline` (the default) |
| Gemini | `AI_PROVIDER_MODE=gemini` + a real `GEMINI_API_KEY` |
| OpenAI | `AI_PROVIDER_MODE=openai` + a real `OPENAI_API_KEY` |
| Force live despite a placeholder key | `AI_FORCE_LIVE=1` — avoid unless certain the key is real |

Per-capability routing applies in live mode: `AI_TEXT_PROVIDER`,
`AI_VISION_PROVIDER`, and `AI_MULTIMODAL_PROVIDER` each accept a provider name.
`ProviderFactory.get_provider_for_modalities()` selects by capability, and
`with_fallback()` walks the fallback chain on retryable errors
(unavailable, rate-limited, timeout).

**Live mode may incur provider charges.** The repository never calls a paid API
during normal development or CI.

## Credentials are never committed

- Provider keys are read only from the environment, via `pydantic-settings`.
- `.gitignore` excludes `.env` and `.env.*`; only `*.example` templates are
  tracked.
- Keys are never logged, never written to disk, and never returned in a
  response.
- A repository-wide scan for `sk-…`, `AIza…`, `AKIA…`, and private-key headers
  returns no matches, in the working tree and across all commits.

## Real-provider tests are optional and out of CI

**There are no tests that call Gemini or OpenAI.** The live adapters are
untested against real APIs, and their response-parsing paths are therefore
unverified. This is a known gap, recorded in [testing.md](testing.md).

This is deliberate, not an oversight:

- Live tests need secrets, which CI must not require.
- Live tests cost money on every run.
- Live tests are non-deterministic, so they are poor regression guards.

The consequence is stated plainly: **the offline provider's conformance proves
the abstraction, not the vendor adapters.** If you depend on Gemini or OpenAI
in production, write your own integration tests against your own credentials
and run them outside CI.

If such tests are ever added, they should be gated behind an environment
variable, skipped by default, and excluded from the workflow in
[`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Adding a provider

1. Implement `MultimodalAIProvider` in `providers/<name>_provider.py`.
2. Declare accurate `ProviderCapabilities` — especially `supports_vision` and
   `supports_structured_output`, which drive routing.
3. Register it in `provider_factory.py`.
4. Add a credential check to `_has_usable_credential` if it uses a key.
5. Add a conformance test that runs against the **offline** path first, so the
   contract is verified without network access.
