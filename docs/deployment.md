# Deployment

## Current state

**Only local development is verified.** This document describes what works
today, then clearly separates what does not.

> Cloud deployment is not currently part of the verified repository state.

## Verified: local development

### Via the setup script

```bash
./scripts/setup-and-run.sh
```

| Component | Address |
| --- | --- |
| Web portal (Vite dev server) | http://localhost:3000 |
| Clinical API (Uvicorn) | http://localhost:8001 |
| API health | http://localhost:8001/api/health |
| Interactive API docs | http://localhost:8001/docs |

Override ports with `BACKEND_PORT` / `FRONTEND_PORT`. If you change
`BACKEND_PORT`, also update `VITE_API_URL` in `web-portal/.env.local` so the
portal can reach the API.

### Via the Makefile

```bash
make setup     # install dependencies
make run       # start both services
make health    # verify both are up
make stop      # stop DEDAN processes
```

### What runs in what mode

The default is **offline mode**: no AI provider credentials, no outbound
network calls, no cost. `setup-and-run.sh` exports `AI_PROVIDER_MODE=offline`
unless the operator overrides it.

## Not implemented: containers

**There is no working Dockerfile for the verified system.** `backend/Dockerfile`
exists but belongs to the superseded v1 backend and has not been verified.

Docker is not used, not tested, and not required by any documented workflow.

## Not implemented: Kubernetes

`kubernetes/` contains manifests for `healthengine-v2`, `hub-system`,
`risk-sentinel`, `messaging-backend`, and `chronic-care`, plus a namespace
definition. These have **never been applied to a cluster**. Several reference
services that are not part of the verified system.

Do not treat this directory as a working deployment.

## Operational characteristics of the current design

Relevant to any future deployment, because they constrain it:

| Property | Current state | Implication |
| --- | --- | --- |
| Rate limiting | In-process dictionary | Resets on restart; per-replica only |
| Image storage | Local filesystem (`/tmp/dedan_images`) | Not shared, not durable, not encrypted |
| Image metadata | In-process dict | Lost on restart; orphans files |
| Conversation memory | In-process, bounded | Not durable, not shared |
| Audit log | stdout only | Not queryable, not tamper-evident |
| Session store | Signed cookie via `SessionMiddleware` | Requires `ADMIN_API_KEY` in production |
| Database | **None on the verified path** | No persistence layer exists |
| TLS | None in-repo | Expected at a terminating proxy |
| Auth | **None** | Must be added before any exposure |

Running more than one replica would produce inconsistent rate limits, image
availability, and conversation state.

## Production requirements

**None of the following exists.** Listed so the gap is explicit rather than
implied.

### Containerisation

- A multi-stage `Dockerfile` for `backend-v2`, running as a non-root user
- A build stage for `web-portal` serving static assets from a CDN or nginx
- Pinned base images by digest, with a defined update cadence
- A `.dockerignore` excluding `.env`, `.venv/`, `node_modules/`, and tests
- Image scanning in CI

### Orchestration

- Readiness and liveness probes wired to `/api/health`
- Resource requests and limits
- A `Secret`/external-secrets source — **never** environment variables baked
  into an image
- A persistent volume or object store for images
- Horizontal scaling, which first requires externalising all in-process state

### Platform

- TLS termination and HSTS
- Authentication and per-patient authorization
- A secrets manager with rotation
- Centralised structured logging with retention limits
- Metrics and distributed tracing
- A migration path for the audit log to durable storage

### Data protection

- Encryption at rest for images and any persisted records
- A documented retention and deletion policy
- Data-subject access and deletion procedures
- DPAs or BAAs with the AI provider

### Clinical and regulatory

- Prospective clinical validation
- Regulatory assessment for the target jurisdictions
- Clinical governance for content updates
- Adverse-event reporting

## Verifying a local deployment

```bash
./scripts/health-check.sh
```

Reports `READY` only when the backend port, `/api/health`, the provider
registry, and the frontend are all reachable. A non-READY result names the
failing check.
