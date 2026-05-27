# PR #10 Revert Workflow

## Objective

Safely revert merged pull request #10 in `ManuDiasCruz/ai-training-workspace-may` while preserving repository history and avoiding unintended removal of unrelated work merged after PR #10.

## PR Reverted

- Pull request: https://github.com/ManuDiasCruz/ai-training-workspace-may/pull/10
- Merge commit: `d8caf4a6fc4d6a2e199a4d2bd65946995b838e1a`
- Rollback branch: `codex/revert-pr-10-shopping-api-mcg`
- Rollback PR: https://github.com/ManuDiasCruz/ai-training-workspace-may/pull/90

## Scope of PR #10

PR #10 introduced a complete Shopping Customers FastAPI/SQLite service:

- FastAPI application under `app/`
- SQLAlchemy customer model and SQLite database session setup
- Pydantic schemas and CRUD helpers
- CSV importer under `scripts/`
- Mall customer CSV dataset under `data/`
- Python dependency file `requirements.txt`
- API test suite under `tests/`
- `.gitignore`
- Replacement `README.md` content documenting the service

## Downstream Impact Assessment

The rollback removes the API surface and local data tooling introduced by PR #10. Any consumer depending on the following may be affected:

- `/health`, `/stats`, or `/customers` endpoints
- `DATABASE_URL` configuration
- `shopping.db` local SQLite database behavior
- `requirements.txt` dependencies from PR #10
- `scripts.import_data` CSV import workflow
- API tests and CI jobs that assume the PR #10 test suite exists

A newer post-merge commit on `main`, `9aaf0ccc`, deleted `README.md`. The revert preserved that newer change instead of restoring the pre-PR one-line README.

## Revert Strategy

1. Cloned the repository and inspected `main` history.
2. Confirmed PR #10 merged through merge commit `d8caf4a6`.
3. Compared commits after `d8caf4a6` and found only `9aaf0ccc`, which deleted `README.md`.
4. Created dedicated branch `codex/revert-pr-10-shopping-api-mcg`.
5. Ran a merge revert:

   ```bash
   git revert -m 1 d8caf4a6 --no-edit
   ```

6. Resolved the expected `README.md` modify/delete conflict by keeping `README.md` deleted to preserve the newer `main` commit.
7. Continued the revert and produced rollback commit `eef3a6f5`.
8. Pushed the rollback branch and opened PR #90.

## Validation Performed

The following checks were run after the revert:

```bash
git diff --check origin/main..HEAD
git fsck --no-progress
python -m pytest -q
```

Results:

- `git diff --check origin/main..HEAD` passed.
- `git fsck --no-progress` passed.
- `python -m pytest -q` reported no tests to run because the PR #10 test suite is removed by the rollback.
- GitHub reported no checks configured for the `main` branch.

## Regression Risks

- Consumers of the removed FastAPI endpoints will receive missing route or service failures after merge.
- CI or deployment scripts referencing removed Python files, `requirements.txt`, or the importer may fail until cleaned up.
- Local developers with existing `shopping.db` files may need to remove stale local artifacts manually.
- Documentation is now absent because `README.md` was already deleted after PR #10 and that deletion was intentionally preserved.

## Recommended Follow-Up

- Validate any deployment or CI configuration for references to removed files.
- Notify downstream users that the shopping customers API is no longer available.
- Decide whether a replacement README or repository status document should be added.
- If the shopping customers service is still needed, reintroduce it later through a corrected PR with explicit stability validation.

## Notification

An email was sent to `madi636@expert.micro1.ai` summarizing the rollback, operational impact, validation performed, remaining risks, and recommended follow-up actions.
