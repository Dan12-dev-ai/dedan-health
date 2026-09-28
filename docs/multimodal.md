# Multimodal Input

This document describes what DEDAN actually accepts today, per modality, and —
just as importantly — what it does not.

## Summary

| Modality | Client input | Backend handling | Vision/speech model used |
| --- | --- | --- | --- |
| **Text** | `symptom_description` | Sent to provider as text | N/A |
| **Image** | `image_ids` or `image_data_list` | Validated, quality-gated, decoded, base64-encoded to provider | Only in live mode |
| **Voice** | `voice_transcript` (string) | Treated as text alongside the symptom description | **None — no speech-to-text** |
| Audio bytes | — | **Not accepted** | — |
| Video | — | **Not accepted** | — |
| Document | — | **Not accepted** | — |

`Modality` in `providers/models.py` *defines* `text`, `image`, `audio`, `video`,
and `document`, and `AudioInput` exists as a model, but the Clinical API exposes
no route that accepts audio, video, or document bytes. The modality enum is
forward-looking; it is not evidence of implemented support.

## Text

```
Input        → symptom_description (10–3000 chars)
Validation   → Pydantic min_length / max_length; type constraints
Preprocess   → combined with symptom_duration, symptom_severity, voice_transcript,
               and prior conversation turns into a single context string
AI model     → provider.analyze_multimodal()
Structured   → possible_explanations[], treatment_education[], sources[]
Safety       → red-flag scan, uncertainty scan, prescribing scan, disclaimer check
Response     → ClinicalResponse
```

Fully implemented and covered by the test suite.

## Image

```
Input        → multipart upload or base64 payload
Validation   → magic-byte MIME sniff, allow-list, ≤10 MB, ≥224×224, ≥1 KiB,
               aspect-ratio warning, filename sanitisation
Preprocess   → stored under IMAGE_STORAGE_PATH with a UUID filename;
               metadata (quality score, issues, warnings) recorded with a TTL
AI model     → ImageInput(image_data=..., mime_type=...) passed to the provider
Structured   → image_assessment {observations, possible_explanations,
               limitations, quality_issues}
Safety       → provider-level limitation reporting; offline provider explicitly
               declines to interpret the image
Response     → ClinicalResponse with visual_education and safety flags
```

**Offline mode does not interpret images.** The offline provider returns an
`ImageAssessment` whose `limitations` field states that no vision model was
available and the image was not clinically interpreted. This is a deliberate
honesty property: the system never implies it looked at an image when it did
not.

Image interpretation requires a live provider with vision capability
(`AI_PROVIDER_MODE` set to a live mode with valid credentials).

## Voice

**Voice input is partially implemented.**

What exists:

- `AnalyzeRequest.voice_transcript: Optional[str]`
- `providers.MultimodalContextBuilder.build_context(voice_transcript=...)`
- The transcript is folded into the same text context as the typed description
- `SymptomInput.voice_input` exists in `models/models.py` to mark
  transcript-sourced input
- The portal has a `VoiceRecorder` component

What does **not** exist:

- **No server-side speech-to-text.** The backend never accepts or decodes audio
  bytes. There is no transcription model, no audio endpoint, and no dependency
  capable of transcription.
- The `AudioInput` model and `Modality.AUDIO` enum are defined but unwired.
- The portal's `VoiceRecorder` capture is not connected to a transcription step.

Consequently, "voice" in DEDAN today means **"text that originated as speech,
transcribed elsewhere."** Any claim that DEDAN accepts voice input directly
would be inaccurate.

## Path to real voice support

1. Add an audio upload endpoint with size, duration, and format validation.
2. Select a transcription provider behind the same `ProviderFactory` pattern.
3. Mark the derived context as `voice_input=true` so downstream logic can
   account for transcription error.
4. Surface transcription confidence to the user; low-confidence transcripts
   should widen uncertainty rather than silently lowering it.
5. Handle the privacy implication explicitly: raw audio is more sensitive than
   a text transcript and needs a distinct retention policy.

## Adding a modality

The provider contract is designed so a new modality does not require changing
the orchestrator:

1. Extend `Modality`.
2. Add an input model alongside `ImageInput` / `AudioInput`.
3. Implement the analysis method on `MultimodalAIProvider`.
4. Set `supports_*` in `ProviderCapabilities` so routing selects a capable
   provider.
5. Add a pipeline stage in `MultimodalContextBuilder`.
6. Extend the safety validator for modality-specific risks.
7. Add tests covering validation, the happy path, and rejection paths.
