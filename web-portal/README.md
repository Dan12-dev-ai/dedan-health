# DEDAN Health — Web Portal

The React + TypeScript frontend for DEDAN Health. This is the **authoritative
frontend**; the other UI directories in the repository are prototypes.

## Quick start

```bash
npm install
npm run dev          # http://localhost:3000
```

The portal expects the Clinical API to be running. Point it at the API with:

```bash
# .env.local
VITE_API_URL=http://localhost:8001
```

If the API is not running, the assessment flow surfaces a typed network error
rather than failing silently — see [Error handling](#error-handling).

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Vite dev server with HMR |
| `npm run build` | Production build into `dist/` |
| `npm run preview` | Serve the production build locally |
| `npm run lint` | `tsc --noEmit` |
| `npm test` | Jest suite |

## Architecture

```
src/
├── index.tsx                 Entry point
├── App.tsx                   Router and layout
├── pages/                    Route-level screens
│   ├── HomePage              Landing and entry points
│   ├── ConsentPage           Consent capture before analysis
│   ├── AssessPage            Multimodal assessment flow
│   ├── ResultsPage           Structured clinical response
│   ├── HistoryPage           Past sessions
│   ├── SessionDetailPage     A single past session
│   ├── FollowUpPage          Follow-up guidance
│   ├── TriagePage            Triage-oriented view
│   ├── SettingsPage          Preferences
│   ├── HelpPage              Help and emergency information
│   └── PricingPage           Product information
├── components/
│   ├── assessment/           Multimodal input surface
│   │   ├── AssessmentShell
│   │   ├── TextComposer
│   │   ├── ImageAttachment
│   │   ├── AttachmentPreview
│   │   ├── VoiceRecorder
│   │   ├── MultimodalInput
│   │   ├── MultimodalMessage
│   │   └── UploadProgress
│   ├── NetworkBanner         Connectivity indicator
│   └── Section               Layout primitive
├── design-system/            Tokens and shared UI
│   ├── tokens.ts             Design tokens
│   ├── theme.tsx             MUI theme
│   ├── SeverityBadge         Urgency indicator
│   ├── TrustBanner           Educational-content disclaimer
│   ├── EmptyState
│   ├── FormField
│   └── icons
├── services/
│   ├── apiClient.ts          Typed fetch wrapper
│   ├── multimodalService.ts  Image encoding and payload assembly
│   ├── triageService.ts      Triage calls
│   ├── offlineStorage.ts     Offline queue
│   └── future/               NOT IMPLEMENTED — see below
├── state/DedanContext.tsx    Application state
├── i18n/                     Locale manifest and strings
├── types/                    Shared TypeScript types
└── __tests__/                Jest suite
```

## State management

A single React Context (`DedanContext`) holds session and assessment state.
There is no Redux, Zustand, or other external store.

This is proportionate: the app manages one active assessment session. If state
grows to include cross-feature caching, server-state synchronisation, or
optimistic updates across screens, a dedicated store with a query cache (for
example TanStack Query) would be the better fit.

## API communication

`apiClient.ts` wraps `fetch` and returns a discriminated `APIResult<T>`:

```ts
type APIResult<T> = { ok: true; data: T } | { ok: false; error: APIError };
```

Three properties are deliberate:

1. **No silent fake success.** Every method returns `ok: true | false`. A
   caller cannot mistake a failure for data.
2. **Network loss is typed, not swallowed.** `OFFLINE` and `NETWORK_ERROR` are
   distinct codes so the UI can queue a write and retry it.
3. **Cookies are not sent** (`credentials: 'omit'`), so no health data travels
   via ambient cookie credentials.

Errors are normalised into `DedanAPIError` with `status`, `code`, `message`,
and an optional `correlation_id`, then converted to `APIError`.

The base URL comes from `VITE_API_URL`, defaulting to `http://localhost:8000`.

## Assessment flow

1. **Home** — entry point.
2. **Consent** — explicit consent is captured before any analysis. The backend
   independently rejects `consent: false` with `400`, so this is not merely a
   UI gate.
3. **Assess** — the user describes symptoms and optionally attaches images.
   `MultimodalInput` composes `TextComposer`, `ImageAttachment`, and
   `VoiceRecorder`.
4. **Results** — the structured clinical document is rendered, including the
   urgency badge, possible explanations with evidence levels, education,
   medication information, sources, and the disclaimer.

## Multimodal input

- **Text** — free-text symptom description, sent as `symptom_description`.
- **Image** — `ImageAttachment` encodes the file and posts it as base64.
  `multimodalService` deliberately strips any `data:` prefix, because
  `image_data_list` expects raw base64 while `upload-base64` parses data URLs
  differently. This is asserted in the test suite.
- **Voice** — `VoiceRecorder` captures audio. **No transcription is performed
  client-side or server-side**, so voice input is not yet connected to
  `voice_transcript`. See [../docs/multimodal.md](../docs/multimodal.md).

## Result visualisation

`ResultsPage` renders the structured document rather than prose:

- `SeverityBadge` maps `safety.urgency` to a colour and label
- `possible_explanations` are shown **with their evidence level**, so a
  `theoretical` explanation is visibly weaker than a `strong` one
- `uncertainty` is rendered prominently rather than buried
- `TrustBanner` carries the educational-content disclaimer
- `medication_information` entries keep their educational-only framing

## Error handling

- Network failure → typed `OFFLINE` / `NETWORK_ERROR`; the UI can queue via
  `offlineStorage` and retry.
- Non-2xx → `DedanAPIError` carrying the backend's `error_code`.
- Unparseable body → `INVALID_JSON`, never a silent `undefined`.
- `NetworkBanner` surfaces connectivity state.

## Testing

```bash
npm test                       # 25 tests, 2 suites
npx tsc --noEmit               # 0 errors
```

`src/__tests__/multimodalService.test.ts` covers the multimodal payload path.

### Why `apiClient` is mapped to a stub in Jest

`apiClient.ts` reads `import.meta.env`, which Babel cannot lower to CommonJS.
`jest.config.cjs` maps the module to `src/__mocks__/apiClient.stub.ts`, which
has an identical public surface. This keeps application code free of
`import.meta`, so the same modules load under both Vite and Jest.

### Coverage gap

`SeverityBadge`, `ProgressIndicator`, and `AssessmentShell` are covered in
`src/__tests__/components.test.tsx`. The page-level components
(`AssessPage`, `ResultsPage`, `ConsentPage`, …) and the remaining assessment
input components still have no render tests. Adding them is the highest-value
frontend improvement.

## Not implemented

`src/services/future/` contains billing, clinic, EHR, feedback, and risk
services. These are **placeholders** exported from `src/services/index.ts` but
backed by no implemented endpoint. They are separated into a `future/`
directory so that nothing in the application silently depends on a route the
API does not serve.

## Build

```bash
npm run build
```

Output goes to `dist/`, which is git-ignored. The build is verified in CI.

## Dependencies

| Package | Purpose |
| --- | --- |
| `react`, `react-dom` | UI runtime |
| `react-router-dom` | Routing |
| `@mui/material`, `@mui/icons-material`, `@emotion/*` | Components and theming |
| `date-fns` | Date formatting |
| `web-vitals` | Performance instrumentation |
| `vite`, `@vitejs/plugin-react` | Build and dev server |
| `jest`, `babel-jest`, `jest-environment-jsdom` | Testing |
| `@testing-library/react`, `@testing-library/jest-dom` | Installed; component tests not yet written |
| `identity-obj-proxy` | CSS module stubbing in Jest |

