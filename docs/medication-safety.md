# Medication Safety

## The three-way distinction

This is the most important concept in this document.

| Concept | Meaning | Status |
| --- | --- | --- |
| **Medication information** | General, public knowledge about a drug class: what it is for, general warnings, known interactions | **Implemented** |
| **Medication verification** | The user confirming a specific physical package against a label | **Implemented as a checklist** |
| **Clinical prescribing** | A clinician deciding that a specific patient should receive a specific drug at a specific dose | **Not implemented, not attempted** |

DEDAN implements the first two. It does not implement the third, and the
architecture is deliberately built so that it cannot appear to.

## Medication information

`MedicationSafetyService` (`backend-v2/medication_safety_enhanced.py`) serves
educational content from a **local reference table**, not from a model. Each
entry describes a drug class:

```python
"antimalarial": {
    "class": "Antimalarial - Artemisinin-based Combination Therapy (ACT)",
    "generic_examples": ["Artemether-lumefantrine", ...],
    "purpose": "Treats uncomplicated Plasmodium falciparum malaria",
    "warnings": [
        "Complete full 3-day course even if feeling better",
        "Do not use for severe malaria - requires IV artesunate",
        ...
    ],
    "contraindications": [...],
    "interactions": [...],
    "evidence_level": "strong",
    "source_guideline": "WHO Guidelines for Malaria (2023)",
}
```

A `MedicationReferenceProvider` interface is defined so the backing data can be
replaced; `LocalMedicationReferenceProvider` is the only implementation. The
module's own docstring notes that a production system would integrate FDA
DailyMed, WHO Essential Medicines, and similar sources. **That integration does
not exist here.**

### Why this is a `MedicationInfo` and not a prescription

Every `MedicationInfo` carries `is_educational_only: bool = True`, serialized
unconditionally as `is_educational_only: true`. This is asserted in three
independent places:

1. `backend-v2/tests/test_clinical_schema.py::test_medication_info_educational_only`
2. `backend-v2/tests/test_api.py::test_medication_output_is_educational_only` —
   asserts the flag on **every** entry in a live API response
3. `scripts/lib/validate_clinical_response.py` — the system test fails if any
   medication entry is not flagged

## Medication verification

Verification here means **helping the user check what they are actually
holding**. The service emits a package checklist:

- Active ingredient (generic/INN name)
- Strength / dose per unit
- Dosage form
- Purpose / indication
- Warnings and precautions
- Directions for use
- Expiration date
- Batch / lot number
- Manufacturer
- Regulatory approval mark
- Storage conditions

Plus questions to ask a pharmacist, guidance on trusted dispensing points,
and warnings about unlicensed vendors and leftover prescriptions.

Each item is emitted as a `MedicationVerificationItem` in the response's
`medication_verification[]` array.

**This is a user-side verification aid, not a backend verification service.**
DEDAN does not query a pharmacy database, confirm regulatory status, or
interact with any dispensing system.

## Prescribing detection

`SafetyValidator._contains_prescription_details()` scans generated text for
two patterns:

**Dosage language** — `\d+ mg`, `\d+ ml`, `\d+ tablet`, `\d+ capsule`,
`take \d+`, `dose of \d+`, `\d+ times daily`, `every \d+ hours`.

**Drug names** — a list including `amoxicillin`, `ciprofloxacin`, `coartem`,
`paracetamol`, `ibuprofen`, and others, matched only in prescriptive phrasing
(`take X`, `prescribe X`).

A match sets a safety flag on the response. This is a **detection** mechanism,
not a guarantee: it will not catch every phrasing, and a determined model could
express a dose in a way these patterns miss.

## Emergency numbers by location

`SafetyValidator._get_emergency_number()` maps patient location substrings to
local emergency numbers (Kenya, Tanzania, Uganda, Nigeria, Ghana, South Africa,
Ethiopia, Rwanda, US, UK, EU, Canada, Australia), defaulting to a generic
`"your local emergency number (e.g., 911, 999, 112)"`.

**Limitation:** this is substring matching over a free-text location field, not
geolocation. A patient who writes "Nairobi, Kenya" gets the Kenyan number; a
patient who writes only "Nairobi" gets the generic fallback. The mapping is not
exhaustive and should not be relied upon for emergency dispatch.

## Country-specific guidance

`get_pharmacy_verification_workflow()` includes Kenya-specific guidance (PPB
licensing, NHIF, KEMSA, counterfeit reporting via `*254#`). `COUNTRY_CODE`
defaults to `KE`. This is hard-coded reference content for one country, not
localised infrastructure.

## What a production system would need

- A maintained, versioned drug reference with an explicit update process
- Regulatory status verification per jurisdiction
- Interaction checking against the patient's actual medication list, from an
  authoritative interaction database
- Dose range checking against age and weight
- A licensed pharmacist or prescriber in the loop for anything that edges
  toward prescribing
- Jurisdiction-specific labelling and language
- Pharmacovigilance — a route to report suspected adverse reactions
