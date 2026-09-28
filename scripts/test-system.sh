#!/usr/bin/env bash
# =============================================================================
# DEDAN Health — automated system smoke test.
#
#   ./scripts/test-system.sh
#
# Verifies toolchain prerequisites, starts the backend if it is not already
# running, exercises a safe OFFLINE /api/analyze request, and asserts the
# response is a well-formed structured clinical document.
#
# This script is non-destructive: it never deletes anything outside .run/, and
# it only terminates a backend process that THIS script started.
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

failures=0
started_backend=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    log_ok "${label}"
  else
    log_error "${label}"
    failures=$((failures + 1))
  fi
}

# Validates the structured clinical document. Kept in a separate helper script
# so this file stays readable.
VALIDATE_SCRIPT="${SCRIPT_DIR}/lib/validate_clinical_response.py"

echo "DEDAN Health System Test"
echo "=========================================================="
echo

# --- 1. Toolchain ------------------------------------------------------------
echo "-- 1. Toolchain --"
check "python3 available"      command -v python3
check "node available"         command -v node
check "npm available"          command -v npm
check "curl available"         command -v curl

VENV_PY="${DEDAN_ROOT}/.venv/bin/python"
[[ -x "${VENV_PY}" ]] || VENV_PY="${DEDAN_ROOT}/.venv/bin/python3"
if [[ -x "${VENV_PY}" ]]; then
  log_ok "Python virtualenv present"
else
  log_warn "No virtualenv at .venv — falling back to system python3"
  VENV_PY="$(command -v python3)"
fi

if [[ -d "${FRONTEND_DIR}/node_modules" ]]; then
  log_ok "Frontend dependencies installed"
else
  log_warn "Frontend node_modules missing — run ./scripts/setup-and-run.sh"
fi
echo

# --- 2. Start the backend if needed -----------------------------------------
echo "-- 2. Backend --"
if port_open "${BACKEND_PORT}"; then
  log_ok "Backend already running on port ${BACKEND_PORT}"
else
  log_info "Starting the backend in offline mode..."
  mkdir -p "${DEDAN_RUN_DIR}"
  (
    cd "${BACKEND_DIR}"
    AI_PROVIDER_MODE=offline nohup "${VENV_PY}" -m uvicorn main_clinical:app \
      --host 0.0.0.0 --port "${BACKEND_PORT}" \
      > "${DEDAN_RUN_DIR}/backend.test.log" 2>&1 &
    echo $! > "${DEDAN_RUN_DIR}/backend.test.pid"
  )
  started_backend=1
  if wait_for_port "${BACKEND_PORT}" 60 "the backend API"; then
    log_ok "Backend started on port ${BACKEND_PORT}"
  else
    log_error "Backend failed to start. See ${DEDAN_RUN_DIR}/backend.test.log"
    tail -20 "${DEDAN_RUN_DIR}/backend.test.log" 2>/dev/null || true
    exit 1
  fi
fi

cleanup() {
  if (( started_backend )); then
    log_info "Stopping the backend started by this test"
    local pid
    if pid="$(pid_from_file "${DEDAN_RUN_DIR}/backend.test.pid")"; then
      kill -TERM "${pid}" 2>/dev/null || true
      sleep 1
      kill -KILL "${pid}" 2>/dev/null || true
    fi
    rm -f "${DEDAN_RUN_DIR}/backend.test.pid"
  fi
}
trap cleanup EXIT

if curl -fsS --max-time 10 "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
  log_ok "GET /api/health responded"
else
  log_error "GET /api/health did not respond"
  failures=$((failures + 1))
fi

# --- 3. Safe offline analysis request ---------------------------------------
echo "-- 3. Clinical analysis (offline provider) --"

# Deliberately generic, non-urgent content: this script must never transmit
# anything resembling a real patient record.
ANALYZE_RESPONSE="$(
  curl -fsS --max-time 60 -X POST "http://localhost:${BACKEND_PORT}/api/analyze" \
    -H 'Content-Type: application/json' \
    -d '{
          "patient_age": 30,
          "patient_sex": "female",
          "symptom_description": "mild headache for two days",
          "symptom_duration": "2 days",
          "symptom_severity": "mild",
          "consent": true
        }' 2>/dev/null || true
)"

if [[ -z "${ANALYZE_RESPONSE}" ]]; then
  log_error "POST /api/analyze returned no body"
  failures=$((failures + 1))
else
  log_ok "POST /api/analyze returned a response"

  VERIFY_REPORT="$(
    ANALYZE_RESPONSE="${ANALYZE_RESPONSE}" \
    "${VENV_PY}" "${VALIDATE_SCRIPT}" 2>/dev/null || true
  )"

  if [[ "${VERIFY_REPORT}" == PASS* ]]; then
    log_ok "Response is a valid structured clinical document"
    printf '       %s\n' "${VERIFY_REPORT}"
  else
    log_error "Response validation failed"
    printf '       %s\n' "${VERIFY_REPORT:-no report produced}"
    failures=$((failures + 1))
  fi
fi

# --- 4. Validation / error handling -----------------------------------------
echo
echo "-- 4. Error handling --"

status="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
  -X POST "http://localhost:${BACKEND_PORT}/api/analyze" \
  -H 'Content-Type: application/json' -d '{}' 2>/dev/null || echo "000")"
if [[ "${status}" == "422" ]]; then
  log_ok "Invalid request rejected with 422"
else
  log_error "Expected 422 for an invalid request, got ${status}"
  failures=$((failures + 1))
fi

status="$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
  -X POST "http://localhost:${BACKEND_PORT}/api/analyze" \
  -H 'Content-Type: application/json' \
  -d '{"patient_age":30,"patient_sex":"female","symptom_description":"mild headache for two days","consent":false}' 2>/dev/null || echo "000")"
if [[ "${status}" == "400" ]]; then
  log_ok "Missing consent rejected with 400"
else
  log_error "Expected 400 when consent is withheld, got ${status}"
  failures=$((failures + 1))
fi
echo

# --- Summary -----------------------------------------------------------------
echo "=========================================================="
if (( failures == 0 )); then
  echo "System test: PASSED"
  exit 0
else
  echo "System test: FAILED (${failures} check(s) failed)"
  exit 1
fi
