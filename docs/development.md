# Development Guide

Everything needed to clone, run, test, and debug DEDAN Health locally.

## Prerequisites

| Tool | Version | Verified with |
| --- | --- | --- |
| Python | 3.11+ | 3.14.6 |
| Node.js | 18+ | 22.23.2 |
| npm | 9+ | 10.9.8 |
| curl | any | required by the scripts |

No API keys, no Docker, and no database are needed for development.

## One-command setup

```bash
./scripts/setup-and-run.sh
```

This creates `.venv`, installs backend and frontend dependencies, copies the
example environment file, and starts both services in offline mode. Logs and
PID files are written to `.run/` (git-ignored).

## Manual setup

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r backend-v2/requirements.txt
cp backend-v2/.env.example backend-v2/.env

cd web-portal && npm install
```

### Why `requirements.txt` looks the way it does

The dependency list was **derived from actual imports**, not from intent. To
re-verify after changing it:

```bash
cd backend-v2 && ../.venv/bin/python -c "import main_clinical"
```

Modules not reachable from `main_clinical` (the agent graph, billing, EMR,
chronic care) are deliberately excluded — they are not on the runtime path.
See [architecture.md](architecture.md) §6.

## Running

```bash
make run            # both services (recommended)
make run-backend    # uvicorn on :8001, offline mode
make run-frontend   # Vite dev server on :3000
```

| Service | URL |
| --- | --- |
| Web portal | http://localhost:3000 |
| API | http://localhost:8001 |
| API docs | http://localhost:8001/docs (requires `DEBUG=true`) |
| Health | http://localhost:8001/api/health |

### Stopping

```bash
make stop            # or ./scripts/stop.sh
```

`stop.sh` terminates only processes belonging to **this checkout** — via
recorded PID files and by matching the repository path in the command line. It
deliberately avoids `pkill -f uvicorn`, which would kill unrelated projects
running ASGI servers on the same machine.

## Configuration

Settings come from `backend-v2/app/core/config.py` using `pydantic-settings`.
`env_file = ".env"` is resolved **relative to the process working directory**,
so the API must be started from `backend-v2/`. The Makefile and scripts handle
this; if you run `uvicorn` by hand, `cd backend-v2` first.

| Variable | Default | Purpose |
| --- | --- | --- |
| `AI_PROVIDER_MODE` | `offline` | `offline`/`mock`/`local`/`rules` = deterministic; anything else permits live calls |
| `GEMINI_API_KEY` | unset | Gemini credential. Leave blank for offline mode |
| `OPENAI_API_KEY` | unset | OpenAI credential. Leave blank for offline mode |
| `DEBUG` | `false` | Enables `/docs` and detailed error output |
| `ENVIRONMENT` | `development` | `production` enables `TrustedHostMiddleware`, disables docs |
| `RATE_LIMIT_REQUESTS` | `30` | Per-IP request limit |
| `IMAGE_TTL_HOURS` | `24` | Uploaded image retention |
| `CORS_ORIGINS` | localhost:3000/3001 | Comma-separated allow-list |

Comma-separated values are supported for list settings; a `field_validator`
splits them before `pydantic-settings` would attempt a JSON parse.

### Why the system defaults to offline

`ProviderFactory._should_use_offline()` returns `True` when offline mode is
requested, **or** when no *usable* credential exists. "Usable" excludes values
containing `test-key`, `changeme`, `placeholder`, `your-`, and similar markers.

A developer with a stale or placeholder key therefore gets a working system
rather than a wall of `401`s — and CI never depends on live credentials.

## Testing

```bash
make test                                       # both suites
cd backend-v2 && ../.venv/bin/python -m pytest tests/ -v
cd web-portal && npm test
./scripts/test-system.sh                        # end-to-end smoke test
```

Backend tests set `AI_PROVIDER_MODE=offline` and blank the provider credentials
in `tests/conftest.py` **before importing the application**, which makes the
suite hermetic: no credentials, no network, no paid calls. The same file raises
`RATE_LIMIT_REQUESTS` because a full run exceeds the production default — the
limiter stays enabled, it is just given more headroom.

### Verified results

On Python 3.14.6 / Node 22.23.2:

```
backend-v2 $ pytest tests/     →  53 passed
web-portal $ npm test          →  25 passed, 2 suites
web-portal $ npx tsc --noEmit  →  0 errors
web-portal $ npm run build     →  built in ~8s
scripts/test-system.sh         →  System test: PASSED
```

## Static checks

```bash
make lint        # tsc --noEmit + Python byte-compile
make fmt-check   # whitespace / CRLF / final-newline check
make format      # apply the whitespace fix
```

`make format` is a whitespace normaliser, not a code formatter. Adding `ruff` or
`black` would reformat the entire codebase in a single change; that is a
separate decision, not something to bundle into repository preparation.

## Debugging

### Logs

| Location | Contents |
| --- | --- |
| `.run/backend.log` | API stdout/stderr when started by the scripts |
| `.run/frontend.log` | Vite output |
| Application log | JSON-ish lines: request/response pairs, `AUDIT:` entries |

Run the API in the foreground to see output directly:

```bash
cd backend-v2 && AI_PROVIDER_MODE=offline ../.venv/bin/python \
  -m uvicorn main_clinical:app --reload --port 8001
```

### Common problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'PIL'` | Dependencies not installed | `.venv/bin/pip install -r backend-v2/requirements.txt` |
| `Can't load the ASGI app` | Started from the wrong directory | `cd backend-v2` first — modules are flat, not a package |
| `/api/analyze` returns `503` | Provider init failed at startup | Check `.run/backend.log` for the initialisation error |
| Frontend cannot reach the API | `VITE_API_URL` mismatch | `web-portal/.env.local` must point at the backend port |
| `429` during development | Rate limit (30/min) | Raise `RATE_LIMIT_REQUESTS`, or wait |
| Responses say `provider: "offline"` | Working as intended | Supply a credential and set `AI_PROVIDER_MODE` to go live |
| CORS errors in the browser | Origin not in `CORS_ORIGINS` | Add the origin to `backend-v2/.env` |
| Tests fail on credentials | A real key in the shell | `unset GEMINI_API_KEY OPENAI_API_KEY` |

### Inspecting the app without starting a server

```bash
cd backend-v2
AI_PROVIDER_MODE=offline ../.venv/bin/python -c "
import main_clinical
from fastapi.testclient import TestClient
print(TestClient(main_clinical.app).get('/api/health').json())
"
```

## Adding a backend dependency

1. Add it to `backend-v2/requirements.txt` **only if `main_clinical` imports it**.
2. Re-verify the file with the import command above.
3. Confirm the test suite still passes in a clean virtualenv.

## Project layout reminder

`backend-v2/` uses a **flat module layout**, not a package. `tests/conftest.py`
prepends the backend root to `sys.path` so pytest works from any directory.
Preserve this when adding modules.

