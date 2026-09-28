# Provenance and Licensing — `data/clinical_guidelines/`

> ## ⚠️ UNRESOLVED — do not redistribute without confirming rights
>
> The three JSON files in this directory are **excluded from the repository's
> MIT licence** because their provenance and redistribution rights have not been
> established. They are attributed to the World Health Organization, and WHO
> content is subject to its own terms, which have not been verified against
> these specific files.

## What is in this directory

| File | Language | Entries | Self-declared source |
| --- | --- | --- | --- |
| `who_guidelines.json` | `en` | 3 | `"source": "WHO"` |
| `swahili_guidelines.json` | `sw` | 6 | `"source": "WHO"` |
| `amharic_guidelines.json` | `am` | 6 | `"source": "WHO"` |

Each entry carries a `condition`, `symptoms[]`, `triage_criteria`, a
`recommendations` string, a `language` code, and a `source` field.

## What has been verified, and what has not

**Verified by inspection:**

- The files contain **short, plainly-worded triage criteria**, not long-form
  prose. For example, the chest-pain entry lists symptoms and threshold values
  (age risk factor 40, duration 15 minutes) in a few hundred characters.
- They carry a `"source": "WHO"` string.
- They are **not verbatim excerpts** from WHO publications. The wording is
  condensed and, in the Swahili and Amharic files, translated.

**Not verified, and therefore unresolved:**

- **Which** WHO publication, edition, or page each entry derives from. There is
  no URL, document identifier, edition, publication date, or retrieval date
  anywhere in the files.
- **WHO's terms for this content**, and whether they permit redistribution in
  this form.
- **Who authored the translations** and under what terms.
- **Clinical review.** No reviewer, version history, or change log is recorded.

A `"source": "WHO"` field is an **attribution claim, not a citation**, and it
does not establish redistribution rights.

## Usage in this repository

**These files are not used by the verified Clinical API.**

- `backend-v2/main_clinical.py` does not read them.
- The only reference is `backend-v2/agents/guideline_agent.py`, which belongs
  to the **unwired LangChain/CrewAI prototype** and requires
  `chromadb` and `sentence-transformers` — dependencies deliberately excluded
  from `backend-v2/requirements.txt`. See
  [docs/architecture.md](../../docs/architecture.md) §6.
- The Clinical API's own urgency classification comes from
  `backend-v2/safety_validator.py` and `urgency_engine.py`, which do not read
  these files.

**Practical consequence: removing this directory would not change the behaviour
of the verified system.** The files are retained for historical context, not
because the running application depends on them.

## Required before redistribution

1. Identify the specific source document for each entry, with URL, edition, and
   retrieval date.
2. Confirm the licence or terms under which WHO permits reuse of that content,
   and whether an attribution notice is required.
3. Confirm the provenance and terms of the Swahili and Amharic translations.
4. Record the author and reviewer of the triage thresholds.
5. Replace the `source` string with a real citation, or remove the files.

Until then, treat this directory as **uncleared for redistribution**. If that is
not acceptable for the intended use, delete the directory — nothing in the
verified system depends on it.
