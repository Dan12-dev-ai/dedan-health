# Evidence System

## Summary

DEDAN maintains a registry of authoritative health sources and attaches
citations to responses. **It does not currently retrieve, index, or quote
source documents.** This document states precisely what the system does so
that no reader mistakes source *metadata* for verified *evidence*.

## What exists today

`backend-v2/evidence_retrieval_enhanced.py` defines `EvidenceRetriever` with a
curated source registry:

| Source | Type | Priority |
| --- | --- | --- |
| WHO | government | 1 |
| CDC | government | 1 |
| FDA | regulatory | 1 |
| MSF Clinical Guidelines | guideline | 1 |
| NICE | guideline | 2 |
| Mayo Clinic | institution | 2 |
| Cleveland Clinic | institution | 2 |
| PubMed | literature | 3 |

`retrieve(topic, evidence_level, max_sources)` returns a dict containing the
topic, the evidence level, a list of `Source` objects, and a summary string.
Results are cached in-process by `topic:evidence_level`.

The number of sources returned scales inversely with the evidence level — a
`strong` request returns priority-1 sources only, while `theoretical` widens to
include priority-3 literature.

## What it does not do

This is the important part.

- **No network access.** The retriever never fetches a document. There is no
  HTTP client, no crawler, and no API call in the retrieval path.
- **No full text is retrieved or quoted.** Responses contain no passages from
  any source.
- **Citations are constructed, not resolved.** A `Source.url` is built by
  concatenating the source's search template with the topic — for example
  `https://www.who.int/search?q=malaria+fever`. It is a *search link*, not a
  citation to a specific document.
- **`date_published` is never populated.** The `Source` dataclass has the
  field; the retriever always sets it to `None`.
- **No ranking by relevance.** Sources are selected by registry order and
  priority, not by whether they actually discuss the topic.
- **No staleness handling.** There is no publication date, so nothing can be
  considered current or outdated.
- **No verification that a source supports a claim.** Nothing checks that the
  cited source actually says what the response asserts.

## Authoritative vs AI-generated

This distinction is central and is preserved structurally in the schema:

| Content | Produced by | Represented as |
| --- | --- | --- |
| `possible_explanations[]` | AI provider | `evidence_level: strong \| moderate \| limited \| theoretical` |
| `treatment_education[]` | AI provider, enriched by templates | `evidence_level` + `sources[]` |
| `medication_information[]` | Curated local reference data | `source: Source \| None`, `is_educational_only: true` |
| `sources[]` | Evidence registry | `title`, `url`, `type`, `jurisdiction` |
| `visual_education[]` | Curated catalogue | `is_ai_generated`, `ai_disclaimer` |
| `safety` | Safety validator + provider | `urgency`, `red_flags[]` |

`possible_explanations[].evidence_level` defaults to `THEORETICAL` precisely
because an unsourced model suggestion should not be presented as established
evidence. The offline provider in particular returns
`evidence_level: "theoretical"`.

## Honest statement of provenance

**DEDAN does not currently guarantee source provenance.** A `sources[]` entry
means "this topic is associated with this authority", not "this statement was
verified against this document".

Consequently, no part of the UI or documentation should present cited content
as having been confirmed against the cited source. A client that wants a real
citation must follow the link and verify independently.

## Path to real retrieval

To make evidence claims substantiable, the following would be required:

1. **Ingest authoritative documents** into a versioned corpus with publication
   dates and a licence record.
2. **Chunk and index** the corpus (embeddings plus a lexical index) so
   retrieval is possible at all.
3. **Retrieve actual passages** matched against the specific claim, not the
   topic.
4. **Quote verbatim** with a locator (document, section, page).
5. **Attach provenance** to each claim: document ID, version, retrieval
   timestamp.
6. **Handle staleness explicitly** — flag or exclude content past a defined
   freshness window.
7. **Record the retrieval itself** in the audit log so a response can be
   reconstructed later.
8. **Validate the mapping** between claims and passages, and abstain when no
   passage supports a claim.

Until those exist, `sources[]` should be understood as *topic-level pointers to
authorities*, and the system should be described as citing, not as retrieving
evidence.
