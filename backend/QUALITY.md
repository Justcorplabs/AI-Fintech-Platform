# Backend code quality

The repository introduces code-quality controls incrementally so that security
and correctness checks become enforceable without mixing them with a large
formatting-only change.

## Blocking checks

These commands must pass locally and in CI:

```bash
python -m ruff check app tests alembic
python -m bandit -r app -q -lll -iii
```

Ruff currently enforces syntax-critical rules:

- `E9`: syntax and indentation failures;
- `F63`: invalid comparisons and assertions;
- `F7`: invalid control flow and definitions;
- `F82`: undefined names.

Bandit blocks only high-severity, high-confidence findings. Lower-severity
results remain visible for review.

## Advisory checks

These checks run in CI but do not fail the workflow yet:

```bash
python -m black --check app tests alembic
python -m pip_audit -r requirements.txt --progress-spinner off
```

Black is advisory because the current baseline contains approximately 70 files
that require reformatting. Formatting must be handled in a dedicated,
formatting-only change.

Dependency auditing is advisory while existing transitive vulnerabilities are
triaged. CI audits `requirements.txt` instead of the developer virtual
environment so unrelated locally installed packages do not create noise.

## Dependency separation

`requirements.txt` remains the application dependency file used by the
production Docker image and backend test job.

`requirements-dev.txt` contains only code-quality tools:

- Black;
- Ruff;
- Bandit;
- pip-audit.

Keeping these files separate prevents the quality job from reinstalling the
large machine-learning dependency stack already installed by the backend test
job.

## Local setup

From `backend`, install the application and quality dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Dependency findings

Do not upgrade foundational application or machine-learning packages blindly.
Review each direct or transitive dependency change, then run:

```bash
python -m alembic check
python -m pytest tests -q
```

The CI dependency report is uploaded as the `backend-pip-audit` artifact and
retained for 14 days.
