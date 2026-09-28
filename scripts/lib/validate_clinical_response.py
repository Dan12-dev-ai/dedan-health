#!/usr/bin/env python3
"""
Validate a DEDAN Health clinical response document.

Used by ``scripts/test-system.sh`` to assert that ``POST /api/analyze`` returns
a well-formed structured clinical response rather than an ad-hoc blob.

The document is read from the ``ANALYZE_RESPONSE`` environment variable so the
caller can pipe the raw HTTP body in without shell-quoting hazards.

Exit status is always 0; the verdict is reported on stdout so the shell script
can branch on it without special-casing error codes.
"""

import json
import os
import sys

REQUIRED_KEYS = [
    "response_id",
    "session_id",
    "timestamp",
    "health_summary",
    "safety",
    "possible_explanations",
    "uncertainty",
    "treatment_education",
    "medication_information",
    "follow_up",
    "sources",
    "confidence_score",
    "disclaimer",
]

VALID_URGENCIES = {"emergency", "urgent", "routine", "self_care", "see_doctor_soon"}


def main() -> int:
    raw = os.environ.get("ANALYZE_RESPONSE", "")

    try:
        body = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - report, never crash
        print(f"FAIL not valid JSON: {exc}")
        return 0

    missing = [key for key in REQUIRED_KEYS if key not in body]
    if missing:
        print("FAIL missing keys: " + ", ".join(missing))
        return 0

    urgency = body["safety"].get("urgency")
    if urgency not in VALID_URGENCIES:
        print(f"FAIL unexpected urgency: {urgency!r}")
        return 0

    confidence = body["confidence_score"]
    if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
        print(f"FAIL confidence out of range: {confidence!r}")
        return 0

    disclaimer = str(body["disclaimer"]).lower()
    if "healthcare professional" not in disclaimer:
        print("FAIL disclaimer does not reference a healthcare professional")
        return 0

    # Medication entries must never be presented as a prescription.
    for med in body["medication_information"] or []:
        if isinstance(med, dict) and med.get("is_educational_only") is not True:
            print("FAIL a medication entry is not flagged as educational-only")
            return 0

    print(
        f"PASS urgency={urgency} "
        f"confidence={confidence} "
        f"explanations={len(body['possible_explanations'])} "
        f"sources={len(body['sources'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
