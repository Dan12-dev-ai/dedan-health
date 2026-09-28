#!/usr/bin/env bash
# =============================================================================
# DEDAN Health — formatting check.
#
# Verifies that tracked text files have no trailing whitespace, no CRLF line
# endings, and a trailing newline. Fails with a list of offending files.
# This is deliberately dependency-free so it runs identically in CI and
# on a contributor's machine without installing a formatter.
# =============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

log_info "Checking whitespace formatting..."

# Respect .gitignore when git is available; otherwise fall back to a prune list.
if git -C "${DEDAN_ROOT}" rev-parse --git-dir >/dev/null 2>&1; then
  mapfile -t FILES < <(
    git -C "${DEDAN_ROOT}" ls-files --cached --others --exclude-standard
  )
else
  log_warn "Not a git repository; scanning the working tree instead."
  mapfile -t FILES < <(
    cd "${DEDAN_ROOT}" && find . -type f \
      -not -path './.git/*' -not -path './node_modules/*' -not -path './.venv/*' \
      -not -path './venv/*' -not -path '*/venv/*' -not -path '*/__pycache__/*' \
      -not -path './web-portal/dist/*' -not -path './web-portal/node_modules/*' \
      -not -name '*.png' -not -name '*.jpg' -not -name '*.jpeg' -not -name '*.ico' \
      -not -name '*.db' -not -name 'package-lock.json' -not -name 'yarn.lock' \
      | sed 's|^\./||'
  )
fi

offenders=()

for file in "${FILES[@]}"; do
  path="${DEDAN_ROOT}/${file}"
  [[ -f "${path}" ]] || continue

  # Skip binary-ish files.
  if ! grep -Iq . "${path}" 2>/dev/null; then
    continue
  fi

  if grep -q $'\r' "${path}" 2>/dev/null; then
    offenders+=("${file} (CRLF line endings)")
  fi
  if grep -qE '[[:space:]]+$' "${path}" 2>/dev/null; then
    offenders+=("${file} (trailing whitespace)")
  fi
  if [[ -s "${path}" ]] && [[ -n "$(tail -c 1 "${path}")" ]]; then
    offenders+=("${file} (missing final newline)")
  fi
done

if (( ${#offenders[@]} == 0 )); then
  log_ok "Formatting check passed (${#FILES[@]} file(s) inspected)."
  exit 0
fi

log_error "Formatting issues found in ${#offenders[@]} location(s):"
for issue in "${offenders[@]}"; do
  printf '  - %s\n' "${issue}"
done
echo
echo "Run 'make format' to fix these automatically."
exit 1
