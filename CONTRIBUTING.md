# Contributing to DEDAN Health

Thanks for your interest. This project is a health-navigation and clinical
decision-support **prototype**. Contributions that improve its engineering
quality, safety posture, or honesty about its limitations are welcome.

Read [SECURITY.md](SECURITY.md) before opening a pull request.

## Development Setup

```bash
git clone https://github.com/Dan12-dev-ai/dedan-health.git
cd dedan-health
./scripts/setup-and-run.sh
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend-v2/requirements.txt
cp backend-v2/.env.example backend-v2/.env
(cd web-portal && npm install)
```

Run everything in **offline mode** by default. You do not need API keys to
develop, test, or review this project.

## Branches and Commits

- Branch from `main` using a descriptive name: `feat/image-quality-gate`,
  `fix/urgency-escalation`, `docs/api-reference`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) prefixes:
  `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`, `security:`,
  `ci:`.
- Keep commits focused. Explain *why* in the body when the reason is not
  obvious from the diff.

## Testing Requirements

Every pull request must keep these green:

```bash
make test              # backend (pytest) + frontend (Jest)
make lint              # tsc --noEmit + Python byte-compile
./scripts/test-system.sh
```

- **New backend behaviour requires a test** in `backend-v2/tests/`. Tests run
  against the offline provider, so they must be deterministic and must not
  require credentials or network access.
- **New frontend behaviour requires a test** in `web-portal/src/__tests__/`.
- If you change a clinical safety rule, the test must include a case that
  demonstrates the new rule firing.

Do not weaken or skip an existing test to make your change pass. If a test is
genuinely wrong, fix it in a separate, explained commit.

## Clinical Safety Requirements

Changes to safety behaviour are reviewed more strictly than other changes. If
your change touches urgency classification, red-flag detection, medication
output, disclaimers, or escalation, the PR description must include:

1. **What changed** and why.
2. **The clinical rationale** — what is safer now, and what is the risk trade-off?
3. **Test evidence** — the specific test that demonstrates the new behaviour.
4. **What could regress** — presentations where the change might make the system
   *less* safe.

Maintain these invariants:

- Urgency is **never** silently downgraded by a later layer.
- Medication output is always `is_educational_only: true`.
- Every response carries a disclaimer referencing a healthcare professional.
- Emergency red-flag detection is **not** weakened without explicit discussion.

Changes to safety logic should be reviewed by someone with clinical
background. If you do not have one available, say so in the PR.

## Documentation Requirements

- Code changes that alter the API require updating [docs/api.md](docs/api.md).
- Architectural changes require updating [docs/architecture.md](docs/architecture.md)
  and a new ADR in [docs/engineering-decisions.md](docs/engineering-decisions.md).
- Configuration changes require updating the relevant `.env.example`.

**Do not overstate capability.** If something is planned, prototype, or
unverified, say so explicitly. Claims of clinical validation, regulatory
approval, or accuracy that cannot be evidenced will be rejected.

## Security Requirements

- Never commit secrets, credentials, tokens, or private keys.
- Never commit real patient data, real health records, or production logs.
- Use synthetic data in tests and examples.
- Do not add endpoints that bypass the consent gate or the safety validator.
- Report vulnerabilities privately per [SECURITY.md](SECURITY.md) — do not
  open a public issue for an unfixed vulnerability.

## Pull Request Checklist

- [ ] `make test` passes
- [ ] `make lint` passes
- [ ] `./scripts/test-system.sh` passes
- [ ] Tests added for new behaviour
- [ ] Documentation updated
- [ ] Clinical-safety rationale included, if applicable
- [ ] No secrets or real patient data in the diff
- [ ] Commit messages follow Conventional Commits

## Code Style

Match the surrounding code. Specifically:

- **Python** — 4-space indent, type hints on public functions, docstrings that
  explain *why* rather than restating the function name.
- **TypeScript** — 2-space indent, typed exports, no `any` without a comment
  justifying it.
- Keep comments for non-obvious decisions. Do not narrate the obvious.

## Code of Conduct

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

Contributions are accepted under the [MIT License](LICENSE).
