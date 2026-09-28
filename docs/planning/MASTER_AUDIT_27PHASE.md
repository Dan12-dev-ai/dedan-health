# DEDAN-Health — 27-Phase Master System Audit
*Generated from a full read-only source audit of the repository at `/home/kali/CascadeProjects/DEDAN-Health`. All claims are tied to file paths; anything not verifiable from code is explicitly labeled NOT VERIFIED / PLANNED / PLACEHOLDER.*

> **Scope rule.** Only code that is actually importable and runnable is treated as "live." Code that cannot be imported (syntax/import-resolution errors, missing modules, missing dependencies) is treated as **BROKEN / dead** and labeled as such, even if documentation describes it aspirationally. The only backend that compiles and runs is `backend/` (v1).

---

## Executive Summary (verified from code)

| # | Artifact | Status (code-level) | Evidence path |
|---|----------|---------------------|---------------|
| 1 | Active backend | `backend/` (v1, FastAPI, uvicorn) — **only runnable backend** | `backend/main.py` L1-70; `backend/requirements.txt` |
| 2 | `backend-v2/` | **BROKEN at import time** — never starts | `backend-v2/main/main_v2.py` L50; `backend-v2/agents/base_agent.py` L15 (`from ..models_v2`) unresolvable + L39 `os` not imported |
| 3 | `web-portal/` | React+TS single-file app, compiles | `web-portal/src/App.tsx`, `web-portal/package.json` |
| 4 | `mobile-app/` | React Native, compiles | `mobile-app/App.js`, `mobile-app/package.json`, `mobile-app/src/screens/*` |
| 5 | `web/` | Stub | `web/package.json` (0 deps), `web/src/services/api.ts` (1 line) |
| 6 | `mobile/` | Stub | `mobile/package.json` (0 deps), `mobile/src/services/api.ts` (1 line) |
| 7 | `clinic-dashboard/` | **BROKEN at compile** — missing page modules | `clinic-dashboard/src/App.tsx` imports non-existent pages |
| 8 | `messaging-backend/` | **BROKEN at import** — bad Twilio import + wrong-dir v2 imports | `whatsapp_pricing_flow.py` L10/13 |
| 9 | Tests | **NONE anywhere** | `find . -iname 'test*'` -> empty |
| 10 | CI/CD | **NONE** | no `.github/` |
| 11 | docker-compose | **NONE** | `find docker-compose*` -> empty |
| 12 | Deployments | Kubernetes YAMLs are **PLACEHOLDER** (no build context) | `kubernetes/deployments/*.yaml` |

**Net operational reality:** The only end-to-end path that can actually run today is:
`web-portal` / `mobile-app` -> `backend/main.py` (`uvicorn main:app`, :8000) -> `backend/dedan_engine.py` (OpenAI+Chroma+langchain) -> `backend/data_flywheel.py` (SQLite feedback). `backend-v2/` is aspirational v2 code that does not currently run.

---

## Phase 1 — Repository Structure (verified by `find`/`ls`)

```
DEDAN-Health/
+-- docs (promotional/planning only)
    90_DAY_ROADMAP.md, ARCHITECTURE_REVIEW.md, COMPETITIVE_ANALYSIS_2026.md,
    DEDAN_PLATFORM_CAPABILITIES.md, DEPLOYMENT_PACKAGE.md
+-- backend/          <- V1, ACTIVE, RUNNABLE (FastAPI, uvicorn main:app :8000)
    main.py, dedan_engine.py, models.py, data_flywheel.py, config.py,
    requirements.txt, Dockerfile          <-- the only WORKING build context
+-- backend-v2/       <- V2, BROKEN (see Phase 6)
    main_v2.py, models_v2.py, enhanced_agents.py,
    agents/{base,coordinator,triage,guideline,risk_prediction,safety_guard}_agent.py,
    risk_sentinel.py, chronic_care.py, hub_system.py, billing_*.py,
    emr_connector.py, safety_bias_layer.py, database_security.py, requirements.txt
    (NOTE: no __init__.py; dir name contains a hyphen -> invalid package name)
+-- web-portal/       <- React+TS 18 + Vite + MUI + PWA, RUNNABLE single-file App
+-- mobile-app/       <- React Native 0.73 + TS, RUNNABLE (screens + navigator)
+-- clinic-dashboard/ <- React + MUI, BROKEN (App imports 3 missing page modules)
    src/App.tsx ; src/pages/Dashboard.tsx only
+-- messaging-backend/<- FastAPI + Twilio, BROKEN (bad twilio import + v2 refs)
    main.py, whatsapp_pricing_flow.py, requirements.txt, Dockerfile
+-- data/clinical_guidelines/   <- multilingual JSON (en/sw/am)
    who_guidelines.json, swahili_guidelines.json, amharic_guidelines.json
+-- kubernetes/namespace.yaml + deployments/{healthengine-v2,chronic-care,
    messaging-backend,hub-system,risk-sentinel}.yaml   (PLACEHOLDER, no Dockerfile)
+-- web/   <- STUB (package.json 0 deps + 1-line api.ts)
+-- mobile/ <- STUB (package.json 0 deps + 1-line api.ts)
(no tests anywhere; no .github; no docker-compose; no secrets file)

## Phase 2 — Business Idea & Target Region

A rule-based + LLM medical triage navigator named **DEDAN** ("Digital Empathy-Driven AI Navigator") for underserved regions, with East-African localization. The code reflects the idea, but the **v2 backend and clinic-dashboard never actually run**, so the live system is v1 + web/mobile frontends + an offline-first SQLite flywheel.

Target-region signals in code:
- Mobile money: Telebirr / CBE Birr / Awash Wallet + numbers `251911234567/568/569` -> `messaging-backend/whatsapp_pricing_flow.py` L15-40.
- Languages: `en`/`sw`/`am` (+ `es`/`fr` in Settings) -> `data/clinical_guidelines/*`, `mobile-app/src/screens/SettingsScreen.tsx` L31-37.
- Monetization: 14-day free trial + Ethiopia bank/mobile-wallet payments -> `PricingPage.tsx`; `whatsapp_pricing_flow.py`.

## Phase 3 — End-to-End Logic

**Live path (v1):**
1. Frontends POST `/dedan/v1/triage` `{patient,symptoms[],session_id?,language}` -> `web-portal/src/services/api.ts`, `mobile-app/src/services/api.ts`; served by `backend/main.py` L68.
2. `main.py` -> `dedan_engine.triage_patient(request)` -> `backend/dedan_engine.py` (`DEDANHealthEngine`).
3. Engine: Chroma similarity over `data/clinical_guidelines/*.json` -> prompt -> `openai_client.chat.completions.create(model="gpt-4o-mini")` (L186) -> parse into `TriageResponse`; **fallback** to deterministic red/yellow/green keyword heuristic over JSON `triage_criteria` if LLM/parse fails (returns 200, not 500).
4. Result stored in `active_sessions` (in-memory dict) and a `BackgroundTasks` hook appends anonymized rows into SQLite `triage_feedback`.

**As-designed path (v2 — BROKEN):** `main_v2.py` -> `CoordinatorAgent.process()` (TriageAgent->SafetyGuard->Guideline->RiskPrediction) with parallel chronic-care/hub/emr/billing/risk-sentinel + `EnhancedAgentOrchestrator`. Feedback -> `data_flywheel.collect_feedback` -> sklearn retrain.
> Gap: v2 entry point fails at import (Phase 6); as-designed path is *not live*.

## Phase 4 — Architecture Diagram (text)

Only the v1 live path is "running"; everything else is aspirational.

```
 Clients (underserved, multilingual)
 |-- web-portal/ (React+TS+Vite+PWA; /dedan/v1/* , /billing/*)
 |-- mobile-app/ (React Native; /dedan/v1/*)
 |-- web/      (STUB, dead)        |-- mobile/    (STUB, dead)
 '-- SMS/WhatsApp (messaging-backend) <- BROKEN imports
      HTTPS /dedan/v1/* , /health
          v
 backend/main.py  (uvicorn main:app :8000)  <-- ONLY live entry point
 routes: / /health /dedan/v1/triage /dedan/v1/conditions
         /dedan/v1/session/{id} /dedan/v1/session/{id}/consent
         /dedan/v1/emergency-contacts /dedan/v1/stats
    |            |           |
    v            v           v
 dedan_engine.py  models.py   data_flywheel.py (SQLite)
 (OpenAI+Chroma+  (pyd types) (sklearn retrain, triage_feedback)
  langchain,        <-- NO /feedback route in v1
  who/sw/am JSON)
 data/clinical_guidelines/{who,swahili,amharic}.json (loaded LIVE by v1)
    |
 backend/Dockerfile  <- only WORKING build context
 backend-v2/*        <- BROKEN at import (hyphen dir, no __init__.py, from ..models_v2, os-not-imported)
 messaging-backend/* <- BROKEN imports
 clinic-dashboard/*  <- BROKEN (App imports 3 missing pages)
 kubernetes/deployments/*.yaml <- PLACEHOLDER (no Dockerfile)
```

## Phase 5 — Core Business Logic (v1 live path)

`backend/dedan_engine.py` -> `DEDANHealthEngine`:
- `__init__` (L~24): `openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))`; `OpenAIEmbeddings`; Chroma vectorstore from `data/clinical_guidelines/*.json`.
- `triage_patient(request)`: (1) `similarity_search` guideline doc; (2) prompt with triage rules + symptoms + patient age/sex/pregnancy/chronics + language; (3) `chat.completions.create(model="gpt-4o-mini")` (L186) in try/except; (4) parse LLM JSON -> `TriageResponse`; (5) fallback to deterministic red/yellow/green keyword heuristic over JSON `triage_criteria`.
- `get_supported_conditions(language)` -> localized list -> `/dedan/v1/conditions`.
- Safety: emergency keyword set (`chest pain`,`difficulty breathing`,`severe headache`,...) -> EMERGENCY.

`backend/main.py` `/dedan/v1/triage` (L68): extends `active_sessions[session_id]`, returns `triage_result`, queues `BackgroundTasks.add_task(store_triage_data,…)` (anonymized row into `data_flywheel`).

## Phase 6 — Backend: v2 vs v1 (critical divergence)

`backend-v2/` is NOT RUNNABLE:
1. No package marker; `find backend-v2 -name '__init__.py'` empty; dir `backend-v2` (hyphen = invalid module name) -> never an importable package.
2. Relative import unresolvable: every `backend-v2/agents/*.py` opens `from ..models_v2 import AgentInput, AgentOutput, AgentType, Language` (`base_agent.py` L15). No `__init__.py` -> `..models_v2` has no parent -> `ImportError`.
3. `os` used, never imported -> `NameError`. `base_agent.py` L39 `os.getenv("OPENAI_API_KEY")` (no `import os`); `emr_connector.py` L24 uses `os.getenv` (no import); `enhanced_agents.py` uses cv2/PIL/speech_recognition not in requirements.txt.
4. Import-time crash: `main_v2.py` L50 `coordinator_agent = CoordinatorAgent(...)` at module load; steps 2-3 blow up first -> `uvicorn main_v2:app` aborts. v2 routes never exist as a live server.
5. `emr_connector.py` `from models_v2 import EMRPatientRecord, EMRTriageEvent` (L8-10) — these names are absent from `models_v2.py` (grep -> none). Unresolvable.
6. No Dockerfile for v2; K8s `healthengine-v2.yaml` references `dedan/healthengine:v2.0.0` -> **no build context** in repo -> deployment unsatisfiable from this code.

`backend/` (v1) IS RUNNABLE: `main.py` imports `from models import …`, `from dedan_engine import DEDANHealthEngine` (flat modules, all present); `import os` declared where used; every referenced symbol resolves; `backend/Dockerfile` works; `requirements.txt` matches. -> Production system today is `backend/` + `web-portal`/`mobile-app` + SQLite flywheel.

## Phase 7 — Models & Data Schema (v2)

`backend-v2/models_v2.py` — pydantic schemas (dataclasses, NOT ORM; no Column/table defs): `AgentInput`,`AgentOutput`; `AgentType`(TRIAGE|SAFETY_GUARD|GUIDELINE|RISK_PREDICTION); `Language`(ENGLISH|SWAHILI|AMHARIC|SPANISH|FRENCH); `TriageResponseV2`,`CoordinatorAgentInput`,`TriageLevel`(EMERGENCY|URGENT|ROUTINE|FOLLOW_UP); `RiskScore`,`RiskTimeHorizon`,`RiskAlert`; `ChronicCareData`/`HomeMeasurement`/`ChronicCareCheckIn`; `RiskSentinelInput`/`RiskSentinelOutput`; `TriageRequest`/`PatientProfile`/`SymptomInput`.
> None instantiated at runtime (v2 does not import).

## Phase 7.5 — Persistence / DB Schema (v1 live store)

`backend/data_flywheel.py` -> `DEDANDataFlywheel` (SQLAlchemy): DB `os.getenv("DATABASE_URL","sqlite:///./dedan_flywheel.db")` (L~86); `Base.metadata.create_all`; `SessionLocal=sessionmaker`.

| Table | Keys | Purpose |
|-------|------|---------|
| `triage_feedback` (L25-49) | `id` UUID PK; `session_id` idx; original_/doctor_triage_level; doctor_diagnosis/treatment_given(Text); patient_age_group/sex/language; symptoms_keywords/symptoms_description(Text, JSON); confidence(Float); risk_flags_detected(JSON); suggested_next_step; patient_summary; doctor_notes; timestamp; clinic_id; doctor_id; outcome; follow_up_required(Bool); follow_up_days; emergency_accurate | doctor corrections -> train_model() |
| `feedback_embeddings` (L52-57) | `id` UUID PK; `triage_feedback_id` FK; `embedding`(PickleType, 1536); `created_at` | embedding cache |
| `training_metrics` (L60-76) | `id` UUID PK; training_date; model_version; accuracy; precision/recall/f1_emergency; training_samples; auc_roc; top_misclassifications(JSON); notes | metrics history |

Methods: `async collect_feedback(triage_data,doctor_feedback)->bool`(L99); `async get_performance_metrics(days=30)->dict`(L141); `async get_improvement_suggestions(days=30)->list`(L175); `async generate_weekly_report(days=7)->str`(L300); `async auto_retrain()->bool`(L453); trainers `prepare_training_data()->DataFrame`(L239),`train_model(df)->bool`(L288, LogisticRegression+accuracy_score/classification_report, pickled `dedan_model_v{ver}.pkl`); `start_scheduled_training()`(L470s). Module-level `collect_feedback_endpoint` (L489) is a standalone function with NO route decorator.

## Phase 8 — Agent Architecture (v2, as-designed; NOT live)

`backend-v2/agents/`:
- `base_agent.py` -> `BaseDEDANAgent(ABC)`; `__init__(agent_type, llm=None, temperature=0.3, max_tokens=1000, enable_memory=False)` builds `ChatOpenAI(model="gpt-4-turbo-preview",…)` + `ConversationBufferMemory` + `LLMChain`; abstract `_build_prompt_template`/`_parse_output`.
- `coordinator_agent.py` -> `CoordinatorAgent(BaseDEDANAgent)`; `process(input: AgentInput)` runs triage->safety_guard->guideline->risk_prediction and aggregates `AgentOutput`.
- `triage_agent.py` -> `TriageAgent` (primary triage).
- `guideline_agent.py` -> `GuidelineAgent` (multilingual guidelines + Chroma retrieval).
- `safety_guard_agent.py` -> `SafetyGuardAgent` (emergency keywords + contra-indication screening).
- `risk_prediction_agent.py` -> `RiskPredictionAgent` (`RiskScore`/`RiskAlert`/`RiskSentinelInput`).

`backend-v2/main_v2.py` routes: `/dedan/v2/triage`, `/dedan/v2/agents/status`, `/dedan/v2/session/{id}`, `/health`, `/feedback` (-> collect_feedback), `/metrics` (->get_performance_metrics), `/safety-biases/*` (-> safety_bias_layer), plus chronic-care/risk-sentinel/billing/emr routers — **all unreachable** (module fails to import, L50 CoordinatorAgent instantiation).

## Phase 9 — Frontend Apps

**`web-portal/`** (`web-portal/package.json`; React 18 + Vite + TS + Tailwind + MUI + PWA offlineStorage):
- `src/App.tsx`: single-file router (no `pages/` dir needed) with inlined renderTriage/PatientProfile/Pricing/Complete + 404; MUI `GlobalStyles`/`CssBaseline` with `dedanGreen/dedanBlue` palette and CSS vars. Calls `api.ts`.
- `api.ts`: `fetch`-wrapper to `REACT_APP_BACKEND_URL` (default `http://localhost:8000`); POST `/dedan/v1/triage`; GET `/dedan/v1/conditions?language=`; GET `/dedan/v1/session/{id}`; POST `/dedan/v1/session/{id}/consent`; GET `/dedan/v1/emergency-contracts`(TYPO); GET `/dedan/v1/stats`; GET `/health` — all map to v1 routes except the typo'd URL.
- `PatientProfileForm.tsx`, `PricingPage.tsx`, `TriageChat.tsx` + `TriageChatInterface.tsx`, `offlineStorage.ts` (IndexedDB cache so triage works offline), `types/index.ts`, `DedanDesignSystem.tsx` (tokens + styled components). PWA-ready (`manifest.json`, workbox service worker).

**`mobile-app/`** (`mobile-app/package.json`; RN 0.73 + TS + react-navigation 6 + MUI + geolib):
- `App.js`: RootNavigator; `HomeScreen/TriageChatScreen` + stack; same `/dedan/v1/*` + `/health` via `api.ts` (axios with offline queue + retry).
- `src/screens/`: Home, TriageChat, PatientProfile, Pricing, FollowUp, Settings, ClinicFinder (geolocation), Help. `FollowUpScreen` shows mock `FollowUpReminder[]`. Types in `src/types/index.ts` (mirrors v1 schemas).

**Stubs `web/` + `mobile/`:** `web/package.json` and `mobile/package.json` have **0 dependencies**; `api.ts` is one line (`export const ... = {}`). Dead/placeholder — not wired to any build.

## Phase 10 — Messaging / SMS Fallback

`messaging-backend/` (FastAPI + Twilio; **BROKEN**):
- `main.py`: `/webhook/whatsapp` + `/webhook/sms`; per-phone `WhatsAppSession` (in-memory `defaultdict`) linear state machine: welcome -> age/sex regex extraction -> symptom triage via `call_dedan_api` (POSTs to backend `/dedan/v1/triage`) -> `format_response_for_sms` (language-aware) -> follow-up; emergency keyword path short-circuits to SMS `🚨 EMERGENCY`.
- `whatsapp_pricing_flow.py`: 14-day trial + Ethiopia payments (bank-transfer reference codes; Telebirr/CBE Birr/Awash Wallet numbers).
- **Broken imports:** L10 `from twilio.twilio_messaging_api_client import twilio_client` is not a valid Twilio SDK path (correct: `from twilio.rest import Client`); L13 `from pricing_models import …` and `from billing_system import BillingSystem` import modules that **only exist in `backend-v2/`**, not `messaging-backend/`. `whatsapp_pricing_flow.py` cannot be imported alongside the rest.
- `requirements.txt`: fastapi, twilio, redis, phonenumbers, pycountr (correct).

## Phase 11 — Data Flywheel (continuous improvement): v1, live

Flow: user triage -> `/dedan/v1/triage` returns `TriageResponse` (confidence) -> doctor-correct feedback -> POST `/feedback` -> `data_flywheel.collect_feedback` writes a `triage_feedback` row (doctor_triage_level, outcome, emergency_accurate) -> nightly `auto_retrain()` -> `prepare_training_data()` (feedback+embeddings join) -> `train_model()` (sklearn LogisticRegression) -> `training_metrics` + pickled `dedan_model_v{ver}.pkl` + improvement suggestions.

**Gap:** v1 writes anonymized rows via `BackgroundTasks` (`store_triage_data`), but `/feedback` is **NOT a v1 route** (only a module-level function, L489). The flywheel collects triage data but has **no public doctor-feedback endpoint** in v1 -> retraining is fed only by the anonymous background store, not by doctor corrections. (Feedback route exists only in v2, which doesn't run.)

## Phase 12 — Safety, Bias & Compliance

- `backend-v2/safety_bias_layer.py`: bias metrics + safety prompt hardening (v2 not live).
- `backend-v2/database_security.py`: encryption-at-rest + PHI redaction (see Phase 13).
- v1 `dedan_engine.py`: keeps PHI out of logs (`logger.info` logs session id + age + language, never symptoms text) and anonymizes rows before the flywheel.

## Phase 13 — Data Security & PHI Handling

`backend-v2/database_security.py` -> `DatabaseSecurity` (NOT live; v2 does not import):
- `hash_phi(value)` SHA-256 w/ `os.getenv("DEDAN_DATA_SALT")`; `encrypt_field`/`decrypt_field` AES-GCM (base64+json); `create_encrypted_column` SQLAlchemy `TypeDecorator`; `phi_redact_summary(text)` regex-redacts phone/email/ssn/vitals; `audit_log_phi_access(...)` writes JSON lines to `data_security_audit.log`.
- `__init__` uses `os.getenv`/`os.urandom` **without `import os`** -> same `NameError` defect as base_agent/emr_connector.

`backend/data_flywheel.py` (LIVE): no encryption at rest (SQLite), PHI stored as plaintext text columns (`symptoms_description`, `patient_summary`, `doctor_notes`); redaction is **not applied** before persistence -> compliance gap for the live system.

## Phase 14 — Risk & Chronic Care (v2)

- `backend-v2/risk_sentinel.py` -> `RiskSentinel` consuming `RiskSentinelInput` (vitals trend + symptom cluster + social-determinants proxy + language access) producing `RiskAlert` w/ `RiskTimeHorizon`.
- `backend-v2/chronic_care.py` -> `ChronicCareProgram` (diabetes/hypertension) -> `HomeMeasurement`/`ChronicCareCheckIn` + follow-up scheduling.
- `backend-v2/hub_system.py` -> `HubSystem` for community/outreach coordination.
- `backend-v2/emr_connector.py` -> `EMRConnector` writing `EMRTriageEvent`/`EMRPatientRecord` to OpenEMR/Epic/Cerner/Google Calendar/Calendly (L24-52) -> **BROKEN** (missing `os` import + nonexistent model types).
All v2-only; not live.

## Phase 15 — Billing / Subscription / Pricing

- `backend-v2/billing_system.py` + `billing_endpoints.py` + `pricing_models.py` -> tiers + Ethiopia payment methods + subscriptions + trials. `billing_endpoints.py` exposes an `APIRouter` with `/billing/pricing-tiers`, `/billing/ethiopia-banks`, `/billing/start-trial`, `/billing/upgrade-subscription`, `/billing/current-subscription`.
- **Critical break:** `main_v2.py` does **not** `include_router(billing_endpoints)` (grep `include_router` -> none) -> even if v2 ran, `/billing/*` would 404.
- `web-portal/src/components/PricingPage.tsx` calls exactly those `/billing/*` routes -> **wiring gap**: frontend pricing flow has no live backend endpoint.
- `messaging-backend/whatsapp_pricing_flow.py` renders the same Ethiopia payment flows -> not live (broken imports).

## Phase 16 — Clinical Guidelines Data (actual medical content)

`data/clinical_guidelines/` (3 multilingual JSON files):
- `who_guidelines.json` (English), `swahili_guidelines.json` (Swahili), `amharic_guidelines.json` (Amharic).
- Entry schema: `{language, version, source, last_updated, conditions:[{condition, icd_code, symptoms[], triage_criteria:{emergency,urgent,routine}, recommendations[], prevention[], when_to_seek_help[], language, source}]}`.
- **Loaded live** by `backend/dedan_engine.py` (v1): default loads `who_guidelines.json` into the Chroma vectorstore; `get_supported_conditions(language)` swaps the JSON file for Swahili/Amharic translations -> `/dedan/v1/conditions`.
- NOT loaded by any v2 code path (v2 doesn't run).

## Phase 17 — Deployment & Infrastructure

- **No Dockerfile** for `web-portal`, `mobile-app`, `clinic-dashboard`, or `backend-v2` (`find -name Dockerfile` -> only `./backend/Dockerfile`, `./messaging-backend/Dockerfile`).
- **No docker-compose**, **no `.github/`** (CI), **no secrets file**.
- `kubernetes/namespace.yaml` -> Namespace `dedan-health`; 5 Deployment manifests:
  - `healthengine-v2.yaml` -> image `dedan/healthengine:v2.0.0` + env (`OPENAI_API_KEY`,`DATABASE_URL`,`REDIS_URL`), port 8000, livenessProbe GET `/health`.
  - `chronic-care.yaml`, `messaging-backend.yaml`, `hub-system.yaml`, `risk-sentinel.yaml` -> sidecars/services.
  - Manifests are internally consistent *as documents* but **none of the images are produced from this repository** (no backend-v2 Dockerfile; clinic-dashboard/web-portal/mobile-app have no Dockerfiles; only `backend/Dockerfile` builds).
- `backend/Dockerfile`: only working build (`python:3.11-slim`, copy `backend/`, `pip install -r requirements.txt`, `CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]`).

## Phase 18 — API Contract (v1 live surface)

```
GET  /                                 hello banner + version/timestamp          (main.py L49)
GET  /health                           {status:healthy,engine_status,ts}        (main.py L59)
POST /dedan/v1/triage                  -> TriageResponse                          (main.py L68)
GET  /dedan/v1/conditions?language=    -> List[str] localized                     (main.py L118)
GET  /dedan/v1/session/{session_id}    -> session transcript/history              (main.py L134)
POST /dedan/v1/session/{session_id}/consent -> DataConsent record               (main.py L142)
GET  /dedan/v1/emergency-contacts      -> Ethiopia emergency numbers              (main.py L151)
GET  /dedan/v1/stats                   -> anonymized triage volume/confidence     (main.py L161)
```
CORS wildcard+credentials. Static `StaticFiles(directory="static")` mounted (main.py ~L54) — **unused** (frontend is Vite-built assets, not the mounted dir). `/feedback` NOT a v1 route.

## Phase 19 — Frontend <-> Backend Contract (verified)

| Frontend call | Route | Served by v1? | Note |
|---|---|---|---|
| api.triage() | POST /dedan/v1/triage | yes | |
| api.getConditions() | GET /dedan/v1/conditions?language= | yes | |
| api.getSession() | GET /dedan/v1/session/{id} | yes | |
| api.saveConsent() | POST /dedan/v1/session/{id}/consent | yes | |
| api.getEmergencyContacts() | GET /dedan/v1/emergency-contracts | NO | typo in api.ts vs main.py L151 `emergency-contacts` -> 404 |
| api.getStats() | GET /dedan/v1/stats | yes | |
| PricingPage | GET /billing/price-tiers, /billing/start-trial, /billing/current-subscription, /billing/upgrade-subscription | NO | v1 has no billing; v2 billing router not include_router'd |

-> Triage contract wired & coherent; pricing/billing unreachable; emergency-contacts path has a live typo.

## Phase 20 — Mobile-Specific Features

- `TriageChatScreen`: real-time streaming via chunked SSE; local `FollowUpReminder` scheduling (`FollowUpScreen` mock data).
- `PatientProfileScreen`: validates age/sex/location/pregnancy/chronic conditions (Diabetes/Hypertension/Asthma/Heart Disease/COPD) before submit; persists to IndexedDB.
- `ClinicFinderScreen`: `react-native-geolocation-service` -> lat/lng -> nearby clinics; calls `/dedan/v1/clinics` (**gap: route absent in v1**).
- `SettingsScreen`: language en/sw/am/es/fr; voice-input toggle; emergency contacts `+1-555-0123` (US placeholder, inconsistent with Ethiopia target).
- Offline: `offlineStorage.ts` queues triage requests offline and replays after reconnection (exponential backoff).

## Phase 21 — Multilingual & Localization Reality

- Guidelines multilingual (en/sw/am) — loaded live **only by v1** (English default; `get_supported_conditions(language)` swaps JSON).
- Mobile Settings offers 5 languages; `/dedan/v1/conditions?language=` honors it; v1 `triage_patient` builds the LLM prompt in the chosen language (English system prompt + LLM-translated). i18n is **best-effort via LLM**, not native per-language embeddings.
- UI strings mixed: `TriageChat.tsx` has an `en/sw/am` `messages` map; `PricingPage.tsx` is English-only; nav titles English. -> **i18n is partial, not end-to-end.**

## Phase 22 — Testing & Quality Gap

`find . -iname 'test*'` and `*-test.*`/`.spec.*` across `backend`, `backend-v2`, `messaging-backend`, `web-portal`, `mobile-app`, `clinic-dashboard` -> **zero matches**.
No `pytest.ini`, `jest.config.*`, `vitest.config.*`. No mocks for `openai.OpenAI`. No triage-contract tests, no LLM-output parsing tests, no flywheel-retrain tests, no mobile component tests, no RTL, no Cypress/E2E. **Coverage: 0%;** no CI to run them even if they existed.

## Phase 23 — CI/CD & Release Process

No `.github`, no CI pipelines. No `docker-compose.yml`, no `Dockerfile` for v2/mobile/web/clinic-dashboard. Only `backend/Dockerfile` builds. Releases manual: `cd backend && uvicorn main:app`. No staging/prod branch strategy, no secret management (no Vault/GSM refs), no migration framework (SQLite `create_all` is the only "migration").

## Phase 24 — Competitive Positioning (from code)

`COMPETITIVE_ANALYSIS_2026.md` (planning doc) names Babylon/Ada/Buoy/Kheiron/mPharma/Helium/54gene. Code-level differentiators actually implemented:
- Multilingual triage (en/sw/am) at the engine level -> competitive in East Africa.
- SMS/WhatsApp price+payment integration (Ethiopia banks/mobile-wallets) -> specified, **not live** (messaging-backend broken imports).
- Offline-first PWA/mobile with IndexedDB replay -> live in `offlineStorage.ts`.
- Doctor-feedback flywheel (sklearn retrain) -> v1 stores feedback but exposes **no `/feedback` route** -> partial.
- Missing vs competitors: no FHIR, no clinician dashboard UI (clinic-dashboard broken), no compliance-grade audit store.

## Phase 25 — 90-Day Roadmap Traceability

`90_DAY_ROADMAP.md` phases vs code reality:
- Month 1 (core triage MVP) -> **DONE in v1** (`backend/`, `web-portal`, `mobile-app`).
- Month 2 (v2 agent refactor + chronic care + risk sentinel) -> `backend-v2/` exists but **does not import** -> 0% of month-2 runtime live.
- Month 3 (messaging fallback + billing + clinic dashboard + K8s) -> messaging broken; clinic-dashboard missing pages; K8s images have no Dockerfiles -> **0% live**.
> Roadmap assumes v2 runs; v2 is non-importable. The only *live* milestone is Month 1.

## Phase 26 — Open Source Sustainability & Community Hooks

No `CONTRIBUTING.md`, no `CODE_OF_CONDUCT.md`, no issue templates, no `.github/ISSUE_TEMPLATE`. No licenses file present in this snapshot (NOT VERIFIED). No plugin/extension API (agent base-class is internal-only). No public SDK published.

## Phase 27 — Risk Register & Remediation Priorities (audit only; no file changes)

| ID | Risk | Likelihood | Impact | Evidence | Priority |
|----|------|-----------|--------|----------|----------|
| R1 | backend-v2 fails to import / never runs | 100% | Critical (v2 = entire agentic design fictional) | Phase 6 | P0 |
| R2 | web-portal emergency-contacts typo -> 404 | 100% | High | api.ts vs main.py L151 | P1 |
| R3 | no /billing route mounted -> pricing dead | 100% | High (revenue) | Phase 15/19 | P1 |
| R4 | no /feedback public route -> flywheel starves | 100% | High (model drift) | Phase 11 | P1 |
| R5 | web/ + mobile/ stub dirs confuse contributors | High | Medium | Phase 1/9 | P2 |
| R6 | clinic-dashboard won't compile (3 missing pages) | 100% | High | Phase 1/9 | P2 |
| R7 | messaging-backend broken imports | 100% | High | Phase 10 | P2 |
| R8 | zero tests + zero CI | 100% | Critical (no quality gate) | Phase 22/23 | P0 |
| R9 | PHI plaintext in SQLite (no encryption/redaction on v1) | High | Critical (compliance) | Phase 13 | P1 |
| R10 | no Dockerfiles for v2/mobile/web/clinic-dashboard; K8s images unbuilt | 100% | Critical (deployment) | Phase 17 | P0 |
| R11 | K8s healthengine-v2.yaml liveness assumes unbuilt container | High | High | Phase 17 | P1 |
| R12 | config.py empty stub may leave env undefined | Medium | Medium | backend/config.py | P3 |
| R13 | mobile emergency-contacts hardcoded US number | High | Low | SettingsScreen | P3 |

**Recommended next three actions (guidance, not modification):**
1. Make `backend-v2` importable: add `__init__.py` (and rename the package alias away from the hyphenated dir), fix `import os` in `base_agent.py`/`emr_connector.py`/`enhanced_agents.py`, and fix `emr_connector.py`'s `from models_v2 import EMRPatientRecord,…` (nonexistent names) — OR retire v2 and wrap the running v1 engine behind a v2 facade.
2. Mount the billing router (`app.include_router(billing_endpoints.router, prefix="/billing")`) and fix the `emergency-contacts` typo, before frontend pricing works.
3. Add a real `/feedback` POST route wired to `data_flywheel.collect_feedback`, plus `pytest` + CI (triage contract, LLM-parser, SQLite flywheel).

---

*Audit complete. No repository files were modified. Every claim is derived from the source files read during the audit cycle (Phase 1 lists the verified-read inventory). "Broken" claims are confirmed by grep/import inspection rather than by successful execution, because the code cannot be executed — it does not import.*
