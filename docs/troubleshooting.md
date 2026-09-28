# Troubleshooting

## Setup

### `python3 -m venv` fails

Confirm Python 3.11+ is on PATH: `python3 --version`. On Debian/Ubuntu, install
with `sudo apt install python3-venv python3-pip`. A `venv` module error usually
means the OS package is missing, not that Python is broken.

### `pip install -r backend-v2/requirements.txt` fails

**`No module named 'PIL'`** — Pillow is a hard import of `image_service.py`. It
is in `requirements.txt`; install into the correct environment and confirm which
interpreter is in use:

```bash
.venv/bin/pip install -r backend-v2/requirements.txt
.venv/bin/python -c "import sys; print(sys.executable)"
```

**Build failures on `numpy` / `pandas`** — these are *not* in
`requirements.txt` and should not be needed. If a script asks for them, it is
importing a prototype module. See [architecture.md](architecture.md) §6.

## Running the API

### `Can't load the ASGI app` / `ModuleNotFoundError: main_clinical`

`backend-v2/` uses a **flat module layout**, not a package, and the ASGI app is
resolved relative to the working directory. Start it from `backend-v2/`:

```bash
cd backend-v2
../.venv/bin/python -m uvicorn main_clinical:app --port 8001
```

The Makefile and the shell scripts handle this; the error only appears when
running `uvicorn` by hand from the repository root.

### `503` from `/api/analyze`

The providers failed to initialise at startup:

```bash
tail -40 .run/backend.log
```

`AI providers not initialized` comes from the `get_provider_factory` dependency,
which raises `503` when `app.state.provider_factory` was never set.

### Port already in use

```bash
lsof -i :8001
```

Change it with `BACKEND_PORT=8002 ./scripts/setup-and-run.sh`, **and** update
`VITE_API_URL` in `web-portal/.env.local` to match, or the portal will still
call 8001.

## Configuration

### Settings are not being picked up

`env_file = ".env"` is resolved relative to the **process working directory**,
so `backend-v2/.env` is only read when the process starts in `backend-v2/`.

```bash
cd backend-v2 && ../.venv/bin/python -c \
  "from app.core.config import get_settings; print(get_settings().AI_PROVIDER_MODE)"
```

### A list setting fails to parse

`CORS_ORIGINS` and `ALLOWED_IMAGE_TYPES` accept **either** a comma-separated
string or a JSON array. A field validator splits the bare form before
`pydantic-settings` attempts a JSON parse, so both work:

```env
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Provider Mode

### Responses say `provider: "offline"`

Working as intended. To go live:

```bash
export AI_PROVIDER_MODE=gemini
export GEMINI_API_KEY=<your real key>
```

Usage **may incur provider charges.**

### The system ignores a key I set

`ProviderFactory._has_usable_credential()` rejects values containing
`test-key`, `test_key`, `your-`, `your_`, `changeme`, `placeholder`, `xxx`,
`<api`, `dummy`, or `example`. This is deliberate — it prevents a placeholder key
from producing a wall of `401`s. Set `AI_FORCE_LIVE=1` to override, but only if
you are certain the credential is real.

### A live provider returns 401/403

The key is absent, expired, or lacks access to the configured model. Check
`GEMINI_MODEL` / `OPENAI_MODEL` in `backend-v2/.env` — the pinned defaults may
no longer be available on your account.

## Frontend

### The portal cannot reach the API

1. Confirm the API is up: `curl http://localhost:8001/api/health`
2. Confirm `VITE_API_URL` in `web-portal/.env.local` matches the backend port
3. Restart Vite — env vars are read at startup
4. Check the browser console for CORS errors; the origin must be in
   `CORS_ORIGINS`

### Changes are not hot-reloading

Vite watches the project root. If a file is outside the watched tree it will not
reload. Restart `npm run dev`.

### Jest cannot parse a module using `import.meta`

`src/services/apiClient.ts` reads `import.meta.env`, which Babel cannot lower to
CommonJS. `jest.config.cjs` maps it to `src/__mocks__/apiClient.stub.ts`. If a
*new* module uses `import.meta`, add it to `moduleNameMapper` too, or isolate
the access the way `apiClient` does.

## Tests

### Backend tests fail on credentials

A real key in your shell can trigger a live call. `conftest.py` blanks
`GEMINI_API_KEY` and `OPENAI_API_KEY`, but only with `setdefault`, so an
already-exported value wins:

```bash
unset GEMINI_API_KEY OPENAI_API_KEY
```

### Backend tests hit the rate limit

The suite raises `RATE_LIMIT_REQUESTS` via `setdefault` for exactly this reason.
If your shell exports a lower value, the limiter will fire:

```bash
unset RATE_LIMIT_REQUESTS
```

### `test-system.sh` passes suspiciously fast

It should print four labelled stages. If it stops after `GET /api/health
responded`, an `if` block is unbalanced and the remaining stages are being
skipped. This bug existed in the repository and was fixed; if you reintroduce
it, `bash -n` will not catch it — check the stage output instead.

### `make test` fails because `.venv` is missing

```bash
make setup
```

## Images

### Upload rejected with "too small"

The pipeline requires ≥224×224 and ≥1 KiB. This is a quality gate — a rejected
image would produce an unreliable analysis. Thumbnail-sized images will not pass.

### Uploads rejected despite a correct `Content-Type`

The MIME type is detected from **magic bytes** and the detected type wins. A
file with the wrong extension is rejected. Verify with `file <image>`.

### Images disappear after a restart

Expected. The metadata index is an in-process dict. Files on disk are orphaned
and not reclaimed on startup. This is a known limitation, documented in
[deployment.md](deployment.md).

## Processes

### `stop.sh` did not stop the service

It only targets processes belonging to this checkout (by PID file and by
repository path in the command line). If you started the API manually from
outside the repository, it will not be matched — which is intentional, so the
script cannot kill an unrelated project's `uvicorn`. Stop it manually with
`kill <pid>`.

### A stale process is holding port 8001

```bash
lsof -i :8001
```

`stop.sh` reports a still-open port as informational, because the port may
belong to an unrelated process.

## Still stuck?

Open an issue with the command you ran, the full output, your Python and Node
versions, and whether you are in offline or live mode. **Do not include real
patient data or credentials.**

